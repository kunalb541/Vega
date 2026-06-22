# Legacy

The original 2021 incarnation of the project, kept here for posterity. It is
**not** maintained and is superseded by the code in [`../app/`](../app/).

| File | Notes |
|------|-------|
| `app.py` | First Dash front-end. Uses the old `dash_core_components` / `dash_html_components` import style and `jitcache` for caching. |
| `download.py` | Early IRSA/ZTF image fetcher. |
| `psf.py` | Early forced-photometry routine. |
| `comp.sh` | Helper that cleared the data dirs and ran the pipeline with `mpiexec` (the original was MPI-parallel rather than `multiprocessing`). |
| `notebooks/mpi-forced-photometry.ipynb` | Notebook version of the photometry, parallelised with `mpi4py`. |
| `notebooks/mcmc-photometry-exploration.ipynb` | Scratch exploration — Metropolis/MCMC sampling experiments related to the flux-uncertainty estimation. |

This version was deployed to Heroku as **bramhaand.com**.
