cd "/Users/yichenluo/Dropbox/dao-governance/"

import delimited using "processed_data/proposals_before_after_discussion.csv", clear

* Ensure cluster variable exists
capture confirm variable space
if _rc {
    di as error "ERROR: variable 'space' not found (needed for clustering)."
    exit 198
}

* Metrics list (base names)
local metrics concensus professionalism objectiveness data_intensity

* Force numeric (in case CSV imported as strings)
foreach m of local metrics {
    capture destring `m'_before `m'_full, replace force
}

* -------------------- COLLECT RESULTS --------------------
tempfile results
postfile H str80(metric) ///
    double( ///
        b_mean b_sd b_p10 b_p50 b_p90 ///
        f_mean f_sd f_p10 f_p50 f_p90 ///
        diff_mean tstat pval ///
    ) str3(stars) using `results', replace

foreach m of local metrics {

    local before `m'_before
    local full   `m'_full

    * Drop rows with missing before or full for this metric
    quietly count if !missing(`before') & !missing(`full')
    if (r(N) < 5) {
        di as txt "Skipping `m' (N<5 after dropping missing)."
        continue
    }

    * Before stats
    quietly summarize `before' if !missing(`before') & !missing(`full'), detail
    local b_mean = r(mean)
    local b_sd   = r(sd)
    local b_p10  = r(p10)
    local b_p50  = r(p50)
    local b_p90  = r(p90)

    * Full stats
    quietly summarize `full' if !missing(`before') & !missing(`full'), detail
    local f_mean = r(mean)
    local f_sd   = r(sd)
    local f_p10  = r(p10)
    local f_p50  = r(p50)
    local f_p90  = r(p90)

    * Difference in means with clustered t-test: diff = full - before
    quietly gen __diff = `full' - `before'
    quietly reg __diff if !missing(__diff), vce(cluster space)

    local d  = _b[_cons]
    local tt = _b[_cons] / _se[_cons]
    local p  = 2 * ttail(e(df_r), abs(`tt'))

    drop __diff

    * Stars
    if (`p' < 0.01)      local stars "***"
    else if (`p' < 0.05) local stars "**"
    else if (`p' < 0.10) local stars "*"
    else                 local stars ""

    * Row label (your LaTeX labels)
    if "`m'" == "concensus"          local label "\$\textit{Concensus}_{i}\$"
    else if "`m'" == "professionalism" local label "\$\textit{Professionalism}_{i}\$"
    else if "`m'" == "objectiveness"   local label "\$\textit{Objectiveness}_{i}\$"
    else if "`m'" == "data_intensity"  local label "\$\textit{Data Intensity}_{i}\$"
    else                               local label "`m'"

    post H ("`label'") ///
        (`b_mean') (`b_sd') (`b_p10') (`b_p50') (`b_p90') ///
        (`f_mean') (`f_sd') (`f_p10') (`f_p50') (`f_p90') ///
        (`d') (`tt') (`p') ("`stars'")
}
postclose H

* -------------------- LATEX EXPORT --------------------
use `results', clear

tempname fh
file open `fh' using "tables/sum_full_vs_before.tex", write replace

file write `fh' "\begin{tabular}{lcccccccccccc}" _n
file write `fh' "\toprule" _n
file write `fh' " & \multicolumn{5}{c}{First-Half} & \multicolumn{5}{c}{Full)} & \multicolumn{2}{c}{Full - First-Half} \\" _n
file write `fh' "\cmidrule(lr){2-6} \cmidrule(lr){7-11} \cmidrule(lr){12-13}" _n
file write `fh' " & Mean & Std. Dev. & P10 & Median & P90 & Mean & Std. Dev. & P10 & Median & P90 & Diff. & t-stat \\" _n
file write `fh' "\midrule" _n

local Nobs = _N
forvalues i = 1/`Nobs' {

    local m = metric[`i']   // <-- this should be RAW, e.g. "concensus"

    * Map raw -> LaTeX label (safe)
    if "`m'" == "concensus"           local label "\$\textit{Concensus}_{i}\$"
    else if "`m'" == "professionalism" local label "\$\textit{Professionalism}_{i}\$"
    else if "`m'" == "objectiveness"   local label "\$\textit{Objectiveness}_{i}\$"
    else if "`m'" == "data_intensity"  local label "\$\textit{Data Intensity}_{i}\$"
    else                               local label "`m'"

    * Format numbers (4 dp)
    local b_mean_fmt : display %12.4f b_mean[`i']
    local b_sd_fmt   : display %12.4f b_sd[`i']
    local b_p10_fmt  : display %12.4f b_p10[`i']
    local b_p50_fmt  : display %12.4f b_p50[`i']
    local b_p90_fmt  : display %12.4f b_p90[`i']

    local f_mean_fmt : display %12.4f f_mean[`i']
    local f_sd_fmt   : display %12.4f f_sd[`i']
    local f_p10_fmt  : display %12.4f f_p10[`i']
    local f_p50_fmt  : display %12.4f f_p50[`i']
    local f_p90_fmt  : display %12.4f f_p90[`i']

    local diff_fmt   : display %12.4f diff_mean[`i']
    local tstat_fmt  : display %12.4f tstat[`i']

    local st = stars[`i']

    file write `fh' ///
        "`label' & `b_mean_fmt' & `b_sd_fmt' & `b_p10_fmt' & `b_p50_fmt' & `b_p90_fmt' & " ///
        "`f_mean_fmt' & `f_sd_fmt' & `f_p10_fmt' & `f_p50_fmt' & `f_p90_fmt' & " ///
        "`diff_fmt' & `tstat_fmt'`st' \\" _n
}

file write `fh' "\bottomrule" _n "\end{tabular}" _n
file close `fh'
