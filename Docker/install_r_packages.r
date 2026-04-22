#!/bin/Rscript

# Parallelise source compilation across every core the builder exposes.
options(Ncpus = max(1L, parallel::detectCores()))

# The CRAN cloud mirror is a CDN and is faster + more reliable than regional hosts.
cran_repo <- "https://cloud.r-project.org"

install.packages(
c(
    'BiocManager',
    'caTools',
    'callr',
    'caret',
    'cowplot',
    'crayon',
    'curl',
    'DescTools',
    'devtools',
    'digest',
    'dplyr',
    'EnvStats',
    'forecast',
    'formatR',
    'ggplot2',
    'ggpubr',
    'ggtern',
    'ggthemes',
    'ggrepel',
    'ggseas',
    'gh',
    'git2r',
    'httr',
    'Hmisc',
    'IRkernel',
    'nycflights13',
    'openssl',
    'plotly',
    'plyr',
    'randomForest',
    'RCurl',
    'remotes',
    'reshape2',
    'rlang',
    'rmarkdown',
    'RSQLite',
    'Rtsne',
    'selectr',
    'shiny',
    'svglite',
    'stringi',
    'stringr',
    'survminer',
    'tictoc',
    'tidyr',
    'tidyverse',
    'usethis',
    'uuid',
    'wesanderson',
    'xgboost'
  ),
  repos = cran_repo
)

# install.packages() does not abort on a failed package; check the ones we
# actually need downstream so the build fails loudly here instead of at the
# next library() call with a confusing "no package called 'devtools'" error.
required <- c("devtools", "IRkernel", "BiocManager")
missing  <- required[!vapply(required, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing) > 0) {
  stop(
    "Required R packages failed to install: ",
    paste(missing, collapse = ", "),
    ". Check the install.packages() output above for the underlying error ",
    "(usually a missing system -dev package)."
  )
}

# Install rethomics
install.packages(
c('behavr',
  'ggetho',
  'damr',
#  'scopr',
  'sleepr',
  'zeitgebr'
  ),
  repos = cran_repo
)

# As of Jan 2024 scopr does not seem to be on CRAN for whatever reason so we
# need to install from github.
library(devtools)
devtools::install_github("rethomics/scopr")

IRkernel::installspec(user = FALSE)
