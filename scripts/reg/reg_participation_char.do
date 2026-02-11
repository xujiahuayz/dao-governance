cd "/Users/yichenluo/Dropbox/dao-governance/"

import delimited using "processed_data/proposals_panel.csv", clear

* Parse date
gen day = date(date, "YMD")
format day %td
gen month = month(day)
gen quarter = quarter(day)

gen year = year(day)
encode gecko_id, gen(token)
encode space,    gen(dao)

* Dependent variables
local dep non_whale_participation whale_participation

* Independent variables
local indep weighted ranked_choice multi_choices 
local discussion concensus professionalism objectiveness data_intensity hhi_post_number post_sentiment post_complexity post_informativeness

* Label variables
label var weighted "\${\it Weighted}_{i,t}\$"
label var quadratic "\${\it Quadratic Voting}_{i,t}\$"
label var ranked_choice "\${\it Ranked Choice}_{i,t}\$"
label var multi_choices "\${\it Multiple Choices}_{i,t}\$"
label var professionalism  "\${\it Professionalism}_{i,t}\$"
label var objectiveness    "\${\it Objectiveness}_{i,t}\$"
label var concensus       "\${\it Concensus}_{i,t}\$"
label var data_intensity   "\${\it Data Intensity}_{i,t}\$"
label var hhi_post_number  "\${\it HHI}_{i,t}^{\# of Post}\$"
label var post_sentiment "\${\it Sentiment}_{i,t}\$"
label var post_complexity "\${\it Complexity}_{i,t}\$"
label var post_informativeness "\${\it Informativeness}_{i,t}\$"

******************************************************
* LOGISTIC REGRESSIONS
******************************************************

eststo clear

foreach d of local dep {

    * VIF test
    qui reg `d' `indep' `discussion'
    estat vif

    * Run regression without discussion
    reghdfe `d' `indep', absorb(year dao)
    eststo `d'
    estadd local fe_token "Y"
    estadd local fe_time  "Y"

    * Run regression with discussion
    reghdfe `d' `indep' `discussion', absorb(year dao)
    eststo `d'_d
    estadd local fe_token "Y"
    estadd local fe_time  "Y"
}

* Export LaTeX table
esttab                                                            ///
    non_whale_participation non_whale_participation_d             ///
    whale_participation whale_participation_d                     ///
    using "tables/reg_participation_char.tex", replace           ///
    se star(* 0.10 ** 0.05 *** 0.01) label nogaps nocon           ///
    nonotes booktabs nomtitles                                    ///
    b(%9.3f) se(%9.2f)                                           ///
    mgroups("\${\it Participation}^{Small}_{i,t}\$"              ///
            "\${\it Participation}^{Whale}_{i,t}\$",             /// 
            span                                                 ///
            pattern(1 0 1 0)                                     ///
            prefix(\multicolumn{@span}{c}{)                      ///
            suffix(})                                            ///
            erepeat(\cmidrule(lr){@span}) )                      ///
    substitute("\_" "_")                                         ///
    stats(fe_token fe_time N r2_a,                               ///
        fmt(0 0 %9.0fc %9.3f)                                   ///
         labels("Token FE" "Year FE" "Observations" "Adjusted R²"))
