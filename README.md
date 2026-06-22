# Vega — Forced Photometry Pipeline

> It took the sky coordinates of any object and returned its brightness history,
> measured directly from raw survey images.

**Vega** (deployed as **bramhaand.com**) was a web app that built the light
curve of an astronomical source on demand. You gave it a position on the sky —
a Right Ascension and Declination — and it fetched the matching images from the
[Zwicky Transient Facility (ZTF)](https://www.ztf.caltech.edu/) survey archive,
ran **PSF forced photometry** at that exact position in every epoch, and plotted
how the object's brightness changed over time. Clicking any point on the curve
showed the difference image it was measured from.

It was built around 2021, before any of the modern LLM tooling existed, ran
live at bramhaand.com for several years, and is now archived here as a snapshot.

<p align="center">
  <img alt="Status" src="https://img.shields.io/badge/status-archived-lightgrey">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11-blue">
  <img alt="Plotly Dash" src="https://img.shields.io/badge/UI-Plotly%20Dash-3f4f75">
  <img alt="Astropy" src="https://img.shields.io/badge/Astropy-photutils-orange">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
</p>

---

## What it did

Most catalogs only list an object's brightness when a survey's own pipeline
flagged a confident detection. **Forced photometry** does something different:
it measures the flux at a *fixed* position in every single image — whether or
not anything was detected — so you also capture the faint epochs and the
non-detections. That's exactly what you need to trace a variable star, a
supernova rising and fading, or an asteroid passing through.

For a requested position the app produced:

- **A light curve** — magnitude vs. time (MJD), split by ZTF filter
  (`g` green, `r` red, `i` infrared), with asymmetric error bars.
- **Upper limits** — for epochs where the source was below the 3σ detection
  threshold, it reported a 5σ *limiting magnitude* instead (drawn as
  downward triangles), so faint/quiescent phases were still informative.
- **A reference image** of the field, and the per-epoch **difference image**
  for any point you clicked on.

## How it worked

```
  RA, DEC
     │
     ▼
┌─────────────┐   query IRSA/IPAC ZTF archive
│ download.py │   ── reference image cutout (25")
│             │   ── difference-image cutouts  (all epochs)
│             │   ── matching PSF models        (all epochs)
└─────┬───────┘   (parallel downloads via multiprocessing)
      │
      ▼
┌─────────────┐   PSF-weighted forced photometry per epoch:
│   psf.py    │     • optimal flux  f = Σ(P·D/σ²) / Σ(P²/σ²)
│             │     • noise σ = √(D/gain + bkgRMS²)
│             │     • uncertainty by likelihood sampling
│             │     • zero-point → magnitude
│             │     • 3σ detection? mag : 5σ limiting mag
└─────┬───────┘
      │  pickled arrays (mag, MJD, band, errors, limits …)
      ▼
┌─────────────┐   Plotly Dash front-end:
│   app.py    │     • interactive light curve
│             │     • reference image (ZScale stretch)
│             │     • click a point → its difference image
└─────────────┘
```

### The measurement, briefly

For each epoch the difference image `D` and the survey's PSF model `P` are
combined into the minimum-variance flux estimate

```
f = Σ (P · D / σ²) / Σ (P² / σ²)
```

with a per-pixel noise model `σ = √(D/gain + bkgRMS²)` (source shot noise plus
a sigma-clipped background RMS from `photutils`). The flux uncertainty is
obtained by sampling the Gaussian likelihood, and the flux is converted to a
calibrated magnitude using the image zero-point (`MAGZP`) from the FITS header.
If the source is detected above 3σ it is reported as a magnitude with
asymmetric `+/-` errors; otherwise the epoch is recorded as a 5σ limiting
magnitude (an upper limit). See [`app/psf.py`](app/psf.py) for the full routine.

## Repository layout

```
.
├── app/
│   ├── app.py          # Plotly Dash web app (UI + callbacks)
│   ├── download.py     # fetches ZTF ref / difference / PSF cutouts from IRSA
│   ├── psf.py          # PSF forced photometry → light-curve arrays
│   ├── dat/            # downloaded FITS land here at runtime (git-ignored)
│   │   ├── ref/  dif/  psf/
│   └── nparray/        # pickled light-curve arrays (git-ignored)
├── legacy/             # the original 2021 version + exploratory notebooks
├── requirements.txt
└── README.md
```

Downloaded telescope data (thousands of FITS cutouts) is intentionally **not**
committed — it is regenerated from the archive for whatever position you query.

## Running it locally

```bash
git clone https://github.com/kunalb541/Vega.git
cd Vega
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python app/app.py          # serves on http://0.0.0.0:9999
```

By default `app.py` renders from previously computed arrays so the UI loads
instantly. To run the full pipeline for a **new** target, uncomment the
download/clean block in `global_store()` (inside [`app/app.py`](app/app.py)),
then enter the object's RA and DEC in the form and hit **Submit** — the app will
pull the images and compute the curve live. The photometry stage can also be run
on its own via [`app/psf.py`](app/psf.py) once images are downloaded.

> **Note:** the front-end was written for the Plotly Dash API of its era. If you
> hit version incompatibilities, the pinned ranges in `requirements.txt` are a
> good starting point; the photometry core (`psf.py` / `download.py`) is plain
> NumPy + Astropy and is far more stable.

## Data source & attribution

All imagery comes from the **Zwicky Transient Facility**, served by the
**NASA/IPAC Infrared Science Archive (IRSA)** at Caltech
(`irsa.ipac.caltech.edu/ibe/...`). ZTF is a public survey; please credit ZTF and
IRSA if you use data obtained through this tool. This project is an independent
client and is not affiliated with ZTF, IPAC, or Caltech.

## History

The project began as **Vega** in 2021 (early experiments live in
[`legacy/`](legacy/), including an MPI-parallel version of the photometry and
some MCMC notebooks) and was deployed publicly as **bramhaand.com**
("ब्रह्मांड", *brahmāṇḍa* — "the cosmos") on Heroku. This repository
consolidates the scattered working copies into a single archived snapshot.

## License

[MIT](LICENSE) © Kunal Bhatia
