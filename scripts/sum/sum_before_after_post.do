/******************************************************************************************
* File: sum_full_vs_before_lowhigh.do
* Goal: For each split var (post_sentiment_high / post_informativeness_high / post_complexity_high),
*       produce a LaTeX table with Low vs High panels.
*       Within each panel: First-Half (before), Full, Full-Before, clustered t-stat (cluster=space).
* Rows: concensus professionalism objectiveness data_intensity
******************************************************************************************/

clear all
set more off
set varabbrev off

cd "/Users/yichenluo/Dropbox/dao-governance/"
import delimited using "processed_data/proposals_before_after_discussion.csv", clear varn(1) case(lower)

capture confirm variable space
if _rc {
    di as error "ERROR: variable 'space' not found (needed for clustering)."
    exit 198
}

capture mkdir "tables"

local metrics concensus professionalism objectiveness data_intensity
foreach m of local metrics {
    capture destring `m'_before `m'_full, replace force
}

local splits post_informativeness_high post_sentiment_high post_complexity_high

foreach s of local splits {
    capture confirm variable `s'
    if _rc {
        di as error "WARNING: split variable `s' not found in imported data."
        continue
    }
    capture confirm numeric variable `s'
    if _rc {
        gen byte `s'_num = .
        replace `s'_num = 1 if inlist(lower(trim(`s')), "true", "1")
        replace `s'_num = 0 if inlist(lower(trim(`s')), "false", "0")
        drop `s'
        rename `s'_num `s'
    }
}

program define _metric_label, rclass
    syntax, METRIC(string)
    local m "`metric'"
    if "`m'" == "concensus"            return local label "\$\textit{Concensus}_{i}\$"
    else if "`m'" == "professionalism" return local label "\$\textit{Professionalism}_{i}\$"
    else if "`m'" == "objectiveness"   return local label "\$\textit{Objectiveness}_{i}\$"
    else if "`m'" == "data_intensity"  return local label "\$\textit{Data Intensity}_{i}\$"
    else                                return local label "`m'"
end

tempfile base
save `base', replace

foreach s of local splits {

    use `base', clear

    capture confirm variable `s'
    if _rc {
        di as error "WARNING: split variable `s' not found. Skipping."
        continue
    }

    * Split label used in LaTeX column headers
    local split_label ""
    if "`s'" == "post_sentiment_high"        local split_label "Post Sentiment"
    if "`s'" == "post_informativeness_high"  local split_label "Post Informativeness"
    if "`s'" == "post_complexity_high"       local split_label "Post Complexity"
    if "`split_label'" == ""                 local split_label "`s'"

    di as txt "Building table for: `split_label' (`s')"

    tempfile results
    postfile H str40(metric) ///
        double( ///
            low_b_mean low_f_mean low_diff low_tstat ///
            high_b_mean high_f_mean high_diff high_tstat ///
        ) str3(low_stars) str3(high_stars) using `results'

    foreach m of local metrics {

        local before `m'_before
        local full   `m'_full

        quietly count if !missing(`before') & !missing(`full') & !missing(`s')
        if (r(N) < 10) {
            di as txt "Skipping `m' in `s' (too few non-missing)."
            continue
        }

        * LOW (s==0)
        quietly count if `s'==0 & !missing(`before') & !missing(`full')
        if (r(N) >= 5) {
            quietly summarize `before' if `s'==0 & !missing(`before') & !missing(`full'), meanonly
            local low_b = r(mean)
            quietly summarize `full' if `s'==0 & !missing(`before') & !missing(`full'), meanonly
            local low_f = r(mean)

            quietly gen __diff = `full' - `before' if `s'==0 & !missing(`before') & !missing(`full')
            quietly reg __diff if !missing(__diff), vce(cluster space)

            local low_d  = _b[_cons]
            local low_tt = _b[_cons] / _se[_cons]
            local low_p  = 2 * ttail(e(df_r), abs(`low_tt'))
            drop __diff
        }
        else {
            local low_b  = .
            local low_f  = .
            local low_d  = .
            local low_tt = .
            local low_p  = .
        }

        local low_stars ""
        if !missing(`low_p') {
            if (`low_p' < 0.01)      local low_stars "***"
            else if (`low_p' < 0.05) local low_stars "**"
            else if (`low_p' < 0.10) local low_stars "*"
        }

        * HIGH (s==1)
        quietly count if `s'==1 & !missing(`before') & !missing(`full')
        if (r(N) >= 5) {
            quietly summarize `before' if `s'==1 & !missing(`before') & !missing(`full'), meanonly
            local high_b = r(mean)
            quietly summarize `full' if `s'==1 & !missing(`before') & !missing(`full'), meanonly
            local high_f = r(mean)

            quietly gen __diff = `full' - `before' if `s'==1 & !missing(`before') & !missing(`full')
            quietly reg __diff if !missing(__diff), vce(cluster space)

            local high_d  = _b[_cons]
            local high_tt = _b[_cons] / _se[_cons]
            local high_p  = 2 * ttail(e(df_r), abs(`high_tt'))
            drop __diff
        }
        else {
            local high_b  = .
            local high_f  = .
            local high_d  = .
            local high_tt = .
            local high_p  = .
        }

        local high_stars ""
        if !missing(`high_p') {
            if (`high_p' < 0.01)      local high_stars "***"
            else if (`high_p' < 0.05) local high_stars "**"
            else if (`high_p' < 0.10) local high_stars "*"
        }

        post H ("`m'") ///
            (`low_b') (`low_f') (`low_d') (`low_tt') ///
            (`high_b') (`high_f') (`high_d') (`high_tt') ///
            ("`low_stars'") ("`high_stars'")
    }

    postclose H
    use `results', clear

    local out "tables/sum_full_vs_before_lowhigh_`s'.tex"

    tempname fh
    file open `fh' using "`out'", write replace

    file write `fh' "\begin{tabular}{lcccccccc}" _n
    file write `fh' "\toprule" _n

    * ----- UPDATED COLUMN GROUP HEADERS -----
    file write `fh' " & \multicolumn{4}{c}{Low `split_label'} & \multicolumn{4}{c}{High `split_label'} \\" _n

    file write `fh' "\cmidrule(lr){2-5} \cmidrule(lr){6-9}" _n
    file write `fh' " & First-Half & Full & Full--First-Half & t-stat & First-Half & Full & Full--First-Half & t-stat \\" _n
    file write `fh' "\midrule" _n

    local Nobs = _N
    forvalues i = 1/`Nobs' {

        local m = metric[`i']
        quietly _metric_label, metric("`m'")
        local label = r(label)

        local lb : display %9.4f low_b_mean[`i']
        local lf : display %9.4f low_f_mean[`i']
        local ld : display %9.4f low_diff[`i']
        local lt : display %9.4f low_tstat[`i']
        local lst = low_stars[`i']

        local hb : display %9.4f high_b_mean[`i']
        local hf : display %9.4f high_f_mean[`i']
        local hd : display %9.4f high_diff[`i']
        local ht : display %9.4f high_tstat[`i']
        local hst = high_stars[`i']

        file write `fh' ///
            "`label' & `lb' & `lf' & `ld' & `lt'`lst' & " ///
            "`hb' & `hf' & `hd' & `ht'`hst' \\" _n
    }

    file write `fh' "\bottomrule" _n
    file write `fh' "\end{tabular}" _n
    file close `fh'

    di as result "Wrote: `out'"
}

di as result "Done."
