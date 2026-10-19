# T5 tables (generated; ENGINEERING_ONLY, model-based, AI-assisted (Claude))

Gains are final true gain J(c_T) − J(c_0) or contrasts, in units of 10⁻³ metric, ± 1 s.e. 'δ_n' columns divide by δ_n = max(0.002, 0.25 × paired sd) (= 0.002 on both calibrated nodes). N = LLM-call cap.

## T1. Calibration

| Scenario | inert share | P(Δ>0 \| informative) | mean μ (informative) | sd of type means | within-type τ (rms) | σ_d local / structural | δ_n |
|---|---|---|---|---|---|---|---|
| digits_off | 0.60 | 0.43 | -3.10 | 6.26 | 8.19 | 7.50 / 11.86 | 2.00 |
| digits_on | 0.45 | 0.28 | -6.47 | 5.34 | 8.87 | 7.50 / 11.86 | 2.00 |
| tabular_off | 0.70 | 0.42 | -1.80 | 3.12 | 5.28 | 4.60 / 7.51 | 2.00 |
| tabular_on | 0.45 | 0.30 | -2.96 | 2.49 | 5.47 | 4.60 / 7.51 | 2.00 |

## T2. Campaign gain by policy (stationary proposer)

| Scenario | W | ρ | A1 | A1+screen | A2 | A2+screen | oracle threshold | oracle thr.+screen | oracle+screen − A2 (δ_n) | oracle+screen − A2+screen (δ_n) | runs / calls, oracle+screen |
|---|---|---|---|---|---|---|---|---|---|---|---|
| digits_off/iid/stationary | 20 | +13.34 ± 0.10 | +13.30 ± 0.09 | +13.30 ± 0.09 | +26.39 ± 0.13 | +26.39 ± 0.13 | +30.88 ± 0.13 | +31.02 ± 0.13 | +2.31 | +2.31 | 12.0 / 40.0 |
| digits_off/iid/stationary | 40 | +26.64 ± 0.14 | +26.60 ± 0.13 | +26.60 ± 0.13 | +53.08 ± 0.19 | +53.08 ± 0.19 | +62.12 ± 0.19 | +62.12 ± 0.19 | +4.52 | +4.52 | 31.9 / 79.8 |
| digits_off/record/stationary | 20 | +13.22 ± 0.10 | +12.80 ± 0.09 | +12.80 ± 0.09 | +24.54 ± 0.12 | +24.54 ± 0.12 | +30.30 ± 0.13 | +30.41 ± 0.13 | +2.94 | +2.94 | 12.0 / 40.0 |
| digits_off/record/stationary | 40 | +26.30 ± 0.13 | +24.98 ± 0.12 | +24.98 ± 0.12 | +46.84 ± 0.17 | +46.84 ± 0.17 | +60.94 ± 0.18 | +60.94 ± 0.18 | +7.05 | +7.05 | 31.9 / 79.9 |
| digits_on/iid/stationary | 20 | +7.00 ± 0.10 | +8.19 ± 0.08 | +8.19 ± 0.08 | +14.51 ± 0.11 | +14.51 ± 0.11 | +17.52 ± 0.11 | +19.32 ± 0.12 | +2.41 | +2.41 | 14.0 / 39.9 |
| digits_on/iid/stationary | 40 | +13.89 ± 0.14 | +16.39 ± 0.12 | +16.39 ± 0.12 | +29.44 ± 0.15 | +29.44 ± 0.15 | +35.58 ± 0.16 | +38.89 ± 0.17 | +4.73 | +4.73 | 28.0 / 80.0 |
| digits_on/record/stationary | 20 | +7.80 ± 0.09 | +7.81 ± 0.08 | +7.81 ± 0.08 | +13.27 ± 0.10 | +13.27 ± 0.10 | +16.95 ± 0.11 | +18.70 ± 0.11 | +2.71 | +2.71 | 14.0 / 39.9 |
| digits_on/record/stationary | 40 | +15.77 ± 0.12 | +14.56 ± 0.10 | +14.56 ± 0.10 | +24.17 ± 0.13 | +24.17 ± 0.13 | +33.00 ± 0.15 | +36.06 ± 0.16 | +5.95 | +5.95 | 27.9 / 80.0 |
| tabular_off/iid/stationary | 20 | +5.17 ± 0.05 | +5.27 ± 0.05 | +5.27 ± 0.05 | +10.54 ± 0.07 | +10.54 ± 0.07 | +12.27 ± 0.07 | +12.27 ± 0.07 | +0.87 | +0.87 | 12.0 / 40.0 |
| tabular_off/iid/stationary | 40 | +10.32 ± 0.07 | +10.45 ± 0.07 | +10.45 ± 0.07 | +21.04 ± 0.10 | +21.04 ± 0.10 | +24.47 ± 0.10 | +24.47 ± 0.10 | +1.72 | +1.72 | 24.0 / 80.0 |
| tabular_off/record/stationary | 20 | +5.27 ± 0.05 | +5.19 ± 0.05 | +5.19 ± 0.05 | +10.19 ± 0.07 | +10.19 ± 0.07 | +12.22 ± 0.07 | +12.22 ± 0.07 | +1.01 | +1.01 | 12.0 / 40.0 |
| tabular_off/record/stationary | 40 | +10.42 ± 0.07 | +10.05 ± 0.07 | +10.05 ± 0.07 | +19.27 ± 0.09 | +19.27 ± 0.09 | +24.13 ± 0.10 | +24.13 ± 0.10 | +2.43 | +2.43 | 24.0 / 80.0 |
| tabular_on/iid/stationary | 20 | +4.77 ± 0.07 | +5.50 ± 0.06 | +5.50 ± 0.06 | +9.72 ± 0.08 | +9.72 ± 0.08 | +11.73 ± 0.08 | +12.41 ± 0.08 | +1.35 | +1.35 | 8.8 / 40.0 |
| tabular_on/iid/stationary | 40 | +9.39 ± 0.09 | +10.79 ± 0.08 | +10.79 ± 0.08 | +19.40 ± 0.11 | +19.40 ± 0.11 | +23.49 ± 0.11 | +24.61 ± 0.11 | +2.60 | +2.60 | 17.6 / 80.0 |
| tabular_on/record/stationary | 20 | +5.26 ± 0.06 | +5.33 ± 0.06 | +5.33 ± 0.06 | +9.24 ± 0.07 | +9.24 ± 0.07 | +11.59 ± 0.07 | +12.36 ± 0.08 | +1.56 | +1.56 | 8.8 / 40.0 |
| tabular_on/record/stationary | 40 | +10.82 ± 0.08 | +10.28 ± 0.08 | +10.28 ± 0.08 | +17.27 ± 0.10 | +17.27 ± 0.10 | +22.74 ± 0.10 | +24.22 ± 0.11 | +3.47 | +3.47 | 17.6 / 80.0 |

## T3. Proposition 7: per-proposal threshold vs constant threshold (same executions)

| Scenario | W | constant t~ | realised gain | Σ exact gap (predicted) | realised / predicted | Σ lower bound | Σ upper bound | realised (δ_n) |
|---|---|---|---|---|---|---|---|---|
| digits_on/iid/stationary | 20 | moment-matched constant t~ | +3.10 ± 0.040 | +3.04 | 1.02 | +2.10 | +5.78 | +1.55 |
| digits_on/iid/stationary | 20 | dev-tuned constant t~ (shift +0.0 σ_d) | +3.10 ± 0.040 | +3.04 | 1.02 | +2.10 | +5.78 | +1.55 |
| digits_on/iid/dimret(k=0.3) | 20 | moment-matched constant t~ | +1.69 ± 0.024 | +2.53 | 0.67 | +1.38 | +8.46 | +0.84 |
| digits_on/iid/dimret(k=0.3) | 20 | dev-tuned constant t~ (shift +0.0 σ_d) | +1.69 ± 0.024 | +2.53 | 0.67 | +1.38 | +8.46 | +0.84 |
| digits_on/iid/memory | 20 | moment-matched constant t~ | +2.06 ± 0.041 | +2.30 | 0.90 | +1.55 | +4.54 | +1.03 |
| digits_on/iid/memory | 20 | dev-tuned constant t~ (shift +0.0 σ_d) | +2.06 ± 0.041 | +2.30 | 0.90 | +1.55 | +4.54 | +1.03 |
| digits_on/record/stationary | 20 | moment-matched constant t~ | +3.80 ± 0.042 | +3.04 | 1.25 | +2.10 | +5.78 | +1.90 |
| digits_on/record/stationary | 20 | dev-tuned constant t~ (shift -0.4 σ_d) | +3.02 ± 0.041 | +4.17 | 0.72 | +2.08 | +8.95 | +1.51 |
| digits_on/record/dimret(k=0.3) | 20 | moment-matched constant t~ | +1.83 ± 0.025 | +2.50 | 0.73 | +1.40 | +8.27 | +0.91 |
| digits_on/record/dimret(k=0.3) | 20 | dev-tuned constant t~ (shift -0.4 σ_d) | +1.52 ± 0.025 | +4.21 | 0.36 | +1.58 | +13.33 | +0.76 |
| digits_on/record/memory | 20 | moment-matched constant t~ | +3.12 ± 0.045 | +2.38 | 1.31 | +1.60 | +4.67 | +1.56 |
| digits_on/record/memory | 20 | dev-tuned constant t~ (shift -0.4 σ_d) | +1.80 ± 0.046 | +3.70 | 0.49 | +1.89 | +7.63 | +0.90 |
| digits_on/iid/stationary | 40 | moment-matched constant t~ | +6.10 ± 0.057 | +6.15 | 0.99 | +4.26 | +11.73 | +3.05 |
| digits_on/iid/stationary | 40 | dev-tuned constant t~ (shift +0.0 σ_d) | +6.10 ± 0.057 | +6.15 | 0.99 | +4.26 | +11.73 | +3.05 |
| tabular_on/iid/stationary | 20 | moment-matched constant t~ | +2.00 ± 0.027 | +2.03 | 0.99 | +1.41 | +3.11 | +1.00 |
| tabular_on/iid/stationary | 20 | dev-tuned constant t~ (shift +0.0 σ_d) | +2.00 ± 0.027 | +2.03 | 0.99 | +1.41 | +3.11 | +1.00 |
| tabular_on/iid/dimret(k=0.3) | 20 | moment-matched constant t~ | +1.38 ± 0.017 | +2.07 | 0.67 | +0.92 | +7.65 | +0.69 |
| tabular_on/iid/dimret(k=0.3) | 20 | dev-tuned constant t~ (shift +0.2 σ_d) | +1.36 ± 0.017 | +1.91 | 0.71 | +1.12 | +6.67 | +0.68 |
| tabular_on/iid/memory | 20 | moment-matched constant t~ | +0.97 ± 0.032 | +1.59 | 0.61 | +1.04 | +2.48 | +0.48 |
| tabular_on/iid/memory | 20 | dev-tuned constant t~ (shift +0.0 σ_d) | +0.97 ± 0.032 | +1.59 | 0.61 | +1.04 | +2.48 | +0.48 |
| tabular_on/record/stationary | 20 | moment-matched constant t~ | +2.34 ± 0.028 | +2.03 | 1.15 | +1.43 | +3.10 | +1.17 |
| tabular_on/record/stationary | 20 | dev-tuned constant t~ (shift -0.2 σ_d) | +2.10 ± 0.026 | +2.37 | 0.89 | +1.37 | +3.78 | +1.05 |
| tabular_on/record/dimret(k=0.3) | 20 | moment-matched constant t~ | +1.41 ± 0.017 | +2.04 | 0.69 | +0.93 | +7.43 | +0.70 |
| tabular_on/record/dimret(k=0.3) | 20 | dev-tuned constant t~ (shift -0.2 σ_d) | +1.32 ± 0.016 | +2.60 | 0.51 | +0.90 | +8.88 | +0.66 |
| tabular_on/record/memory | 20 | moment-matched constant t~ | +1.86 ± 0.035 | +1.63 | 1.14 | +1.08 | +2.54 | +0.93 |
| tabular_on/record/memory | 20 | dev-tuned constant t~ (shift -0.4 σ_d) | +1.04 ± 0.034 | +2.89 | 0.36 | +1.42 | +4.30 | +0.52 |
| tabular_on/iid/stationary | 40 | moment-matched constant t~ | +4.06 ± 0.038 | +4.12 | 0.98 | +2.90 | +6.28 | +2.03 |
| tabular_on/iid/stationary | 40 | dev-tuned constant t~ (shift +0.0 σ_d) | +4.06 ± 0.038 | +4.12 | 0.98 | +2.90 | +6.28 | +2.03 |
| digits_off/iid/stationary | 20 | moment-matched constant t~ | +4.48 ± 0.038 | +4.42 | 1.01 | +1.93 | +7.38 | +2.24 |
| digits_off/iid/stationary | 20 | dev-tuned constant t~ (shift -0.2 σ_d) | +4.31 ± 0.042 | +4.23 | 1.02 | +1.95 | +7.69 | +2.16 |
| digits_off/record/stationary | 20 | moment-matched constant t~ | +5.78 ± 0.044 | +4.41 | 1.31 | +1.93 | +7.39 | +2.89 |
| digits_off/record/stationary | 20 | dev-tuned constant t~ (shift -0.4 σ_d) | +4.17 ± 0.044 | +4.81 | 0.87 | +2.34 | +8.73 | +2.09 |
| digits_off/iid/stationary | 40 | moment-matched constant t~ | +9.00 ± 0.053 | +8.95 | 1.01 | +3.91 | +14.88 | +4.50 |
| digits_off/iid/stationary | 40 | dev-tuned constant t~ (shift -0.2 σ_d) | +8.60 ± 0.059 | +8.51 | 1.01 | +3.90 | +15.47 | +4.30 |
| tabular_off/iid/stationary | 20 | moment-matched constant t~ | +1.73 ± 0.021 | +1.74 | 0.99 | +1.01 | +2.37 | +0.86 |
| tabular_off/iid/stationary | 20 | dev-tuned constant t~ (shift -0.2 σ_d) | +1.76 ± 0.022 | +1.76 | 1.00 | +1.05 | +2.53 | +0.88 |
| tabular_off/record/stationary | 20 | moment-matched constant t~ | +2.09 ± 0.023 | +1.74 | 1.20 | +1.02 | +2.38 | +1.04 |
| tabular_off/record/stationary | 20 | dev-tuned constant t~ (shift -0.4 σ_d) | +1.73 ± 0.023 | +2.10 | 0.82 | +1.26 | +2.98 | +0.86 |
| tabular_off/iid/stationary | 40 | moment-matched constant t~ | +3.47 ± 0.029 | +3.48 | 1.00 | +2.03 | +4.75 | +1.73 |
| tabular_off/iid/stationary | 40 | dev-tuned constant t~ (shift +0.0 σ_d) | +3.47 ± 0.029 | +3.48 | 1.00 | +2.03 | +4.75 | +1.73 |

## T4. Proposition 8: screening

Lagrangian check (no binding run budget, N = 40 proposals; J_g = Σ(Δk − g a)):

| Scenario | g (× tuned) | layer | realised J_g gain | predicted Σ(g − V*)⁺ |
|---|---|---|---|---|
| digits_on/iid/stationary | 0.075 (0.5×) | total (vs always execute) | +1.61 ± 0.013 | +1.61 ± 0.001 |
| digits_on/iid/stationary | 0.075 (0.5×) | learned layer (vs rules) | +0.26 ± 0.012 | +0.26 ± 0.000 |
| digits_on/iid/stationary | 0.150 (1×) | total (vs always execute) | +3.56 ± 0.013 | +3.56 ± 0.002 |
| digits_on/iid/stationary | 0.150 (1×) | learned layer (vs rules) | +0.86 ± 0.013 | +0.86 ± 0.001 |
| digits_on/iid/stationary | 0.300 (2×) | total (vs always execute) | +7.57 ± 0.025 | +7.57 ± 0.004 |
| digits_on/iid/stationary | 0.300 (2×) | learned layer (vs rules) | +2.17 ± 0.025 | +2.18 ± 0.003 |
| tabular_on/iid/stationary | 0.046 (0.5×) | total (vs always execute) | +0.83 ± 0.009 | +0.83 ± 0.001 |
| tabular_on/iid/stationary | 0.046 (0.5×) | learned layer (vs rules) | -0.00 ± 0.009 | +0.01 ± 0.000 |
| tabular_on/iid/stationary | 0.092 (1×) | total (vs always execute) | +2.06 ± 0.014 | +2.07 ± 0.001 |
| tabular_on/iid/stationary | 0.092 (1×) | learned layer (vs rules) | +0.41 ± 0.014 | +0.41 ± 0.001 |
| tabular_on/iid/stationary | 0.184 (2×) | total (vs always execute) | +4.93 ± 0.014 | +4.94 ± 0.002 |
| tabular_on/iid/stationary | 0.184 (2×) | learned layer (vs rules) | +1.62 ± 0.014 | +1.62 ± 0.002 |
| digits_off/iid/stationary | 0.075 (0.5×) | total (vs always execute) | +1.94 ± 0.009 | +1.93 ± 0.001 |
| digits_off/iid/stationary | 0.075 (0.5×) | learned layer (vs rules) | +0.13 ± 0.009 | +0.13 ± 0.000 |
| digits_off/iid/stationary | 0.150 (1×) | total (vs always execute) | +4.04 ± 0.009 | +4.04 ± 0.002 |
| digits_off/iid/stationary | 0.150 (1×) | learned layer (vs rules) | +0.43 ± 0.009 | +0.43 ± 0.001 |
| digits_off/iid/stationary | 0.300 (2×) | total (vs always execute) | +8.25 ± 0.010 | +8.24 ± 0.004 |
| digits_off/iid/stationary | 0.300 (2×) | learned layer (vs rules) | +1.03 ± 0.009 | +1.03 ± 0.002 |
| tabular_off/iid/stationary | 0.115 (0.5×) | total (vs always execute) | +3.32 ± 0.008 | +3.32 ± 0.002 |
| tabular_off/iid/stationary | 0.115 (0.5×) | learned layer (vs rules) | +0.10 ± 0.007 | +0.10 ± 0.000 |
| tabular_off/iid/stationary | 0.230 (1×) | total (vs always execute) | +7.08 ± 0.013 | +7.09 ± 0.003 |
| tabular_off/iid/stationary | 0.230 (1×) | learned layer (vs rules) | +0.64 ± 0.013 | +0.65 ± 0.001 |
| tabular_off/iid/stationary | 0.460 (2×) | total (vs always execute) | +14.90 ± 0.014 | +14.91 ± 0.005 |
| tabular_off/iid/stationary | 0.460 (2×) | learned layer (vs rules) | +2.02 ± 0.013 | +2.03 ± 0.004 |
| digits_on/record/stationary | 0.075 (0.5×) | total (vs always execute) | +1.69 ± 0.013 | +1.61 ± 0.001 |
| digits_on/record/stationary | 0.075 (0.5×) | learned layer (vs rules) | +0.34 ± 0.013 | +0.26 ± 0.000 |
| digits_on/record/stationary | 0.150 (1×) | total (vs always execute) | +3.64 ± 0.013 | +3.56 ± 0.002 |
| digits_on/record/stationary | 0.150 (1×) | learned layer (vs rules) | +0.93 ± 0.013 | +0.86 ± 0.001 |
| digits_on/record/stationary | 0.300 (2×) | total (vs always execute) | +7.82 ± 0.026 | +7.58 ± 0.004 |
| digits_on/record/stationary | 0.300 (2×) | learned layer (vs rules) | +2.41 ± 0.025 | +2.17 ± 0.003 |
| tabular_on/record/stationary | 0.046 (0.5×) | total (vs always execute) | +0.92 ± 0.011 | +0.83 ± 0.001 |
| tabular_on/record/stationary | 0.046 (0.5×) | learned layer (vs rules) | +0.09 ± 0.011 | +0.01 ± 0.000 |
| tabular_on/record/stationary | 0.092 (1×) | total (vs always execute) | +2.22 ± 0.015 | +2.07 ± 0.001 |
| tabular_on/record/stationary | 0.092 (1×) | learned layer (vs rules) | +0.56 ± 0.015 | +0.41 ± 0.001 |
| tabular_on/record/stationary | 0.184 (2×) | total (vs always execute) | +5.09 ± 0.016 | +4.94 ± 0.002 |
| tabular_on/record/stationary | 0.184 (2×) | learned layer (vs rules) | +1.78 ± 0.015 | +1.63 ± 0.002 |

Hard budget (W runs, N = 2W calls; oracle threshold with vs without learned screening, rules on in both):

| Scenario | W | tuned g | realised gain of screening | Σ(g − V*)⁺ over the screening run | learned skips | calls used (screen / no screen) |
|---|---|---|---|---|---|---|
| digits_on/iid/stationary | 20 | 0.150 | +1.92 ± 0.045 | +0.85 | 8.0 | 39.9 / 35.5 |
| digits_on/iid/stationary | 40 | 0.150 | +3.37 ± 0.063 | +1.71 | 16.0 | 80.0 / 71.9 |
| tabular_on/iid/stationary | 20 | 0.092 | +0.74 ± 0.034 | +0.41 | 13.2 | 40.0 / 35.5 |
| tabular_on/iid/stationary | 40 | 0.092 | +1.10 ± 0.047 | +0.82 | 26.4 | 80.0 / 71.9 |
| digits_off/iid/stationary | 20 | 0.150 | +0.10 ± 0.019 | +0.43 | 4.0 | 40.0 / 39.6 |
| digits_off/iid/stationary | 40 | 0.000 | +0.00 ± 0.000 | +0.00 | 0.0 | 79.9 / 79.9 |
| tabular_off/iid/stationary | 20 | 0.000 | +0.00 ± 0.000 | +0.00 | 0.0 | 40.0 / 40.0 |
| tabular_off/iid/stationary | 40 | 0.000 | +0.00 ± 0.000 | +0.00 | 0.0 | 80.0 / 80.0 |
| digits_on/record/stationary | 20 | 0.150 | +1.77 ± 0.042 | +0.86 | 8.0 | 39.9 / 35.5 |
| digits_on/record/stationary | 40 | 0.150 | +3.09 ± 0.055 | +1.72 | 16.0 | 80.0 / 71.9 |
| tabular_on/record/stationary | 20 | 0.092 | +0.79 ± 0.033 | +0.41 | 13.2 | 40.0 / 35.5 |
| tabular_on/record/stationary | 40 | 0.092 | +1.59 ± 0.047 | +0.82 | 26.4 | 80.0 / 71.9 |

## T5. Proposition 9: record bias after keeps (W = 40, N = 80)

Record model: observed new record error e′ vs ϱe + σ_c λ(a); iid model: Δ̂ − Δ at a keep vs σ_d λ((t − Δ)/σ_d).

| Scenario | policy | keeps | mean observed | mean formula | residual ± s.e. | null keeps: mean rise / formula | record bias at end | debiased B~ bias at end | gain | bold share |
|---|---|---|---|---|---|---|---|---|---|---|
| digits_on/record/stationary | rho | 105363 | +13.38 | +13.39 | -0.004 ± 0.016 | +9.04 / +9.04 | +22.18 | -7.14 | +16.05 | 0.120 |
| digits_on/record/stationary | oracle_threshold | 159047 | +12.91 | +12.93 | -0.018 ± 0.014 | +7.03 / +7.06 | +21.12 | -9.25 | +33.56 | 0.120 |
| digits_on/record/dimret(k=0.3) | rho | 89938 | +13.18 | +13.18 | +0.003 ± 0.017 | +9.23 / +9.23 | +21.11 | -6.00 | +10.92 | 0.120 |
| digits_on/record/dimret(k=0.3) | oracle_threshold | 83017 | +11.83 | +11.83 | -0.002 ± 0.018 | +9.32 / +9.35 | +18.96 | -4.56 | +16.95 | 0.120 |
| digits_on/record/memory | rho | 103159 | +12.76 | +12.76 | -0.006 ± 0.018 | +9.68 / +9.68 | +21.32 | -10.07 | +19.95 | 0.238 |
| digits_on/record/memory | oracle_threshold | 138250 | +13.09 | +13.08 | +0.004 ± 0.015 | +8.63 / +8.63 | +22.56 | -13.19 | +37.95 | 0.265 |
| digits_on/record/memory_debiased | rho | 104575 | +13.20 | +13.20 | -0.001 ± 0.016 | +9.20 / +9.20 | +21.89 | -7.93 | +17.03 | 0.151 |
| digits_on/record/memory_debiased | oracle_threshold | 146795 | +12.87 | +12.88 | -0.008 ± 0.015 | +7.86 / +7.90 | +22.02 | -11.50 | +36.02 | 0.205 |
| digits_on/iid/stationary | rho | 139282 | +6.22 | +6.21 | +0.012 ± 0.016 | +10.28 / +10.27 | +43.32 | +0.02 | +13.80 | 0.120 |
| digits_on/iid/stationary | oracle_threshold | 199005 | +5.06 | +5.06 | -0.005 ± 0.014 | +9.27 / +9.28 | +50.30 | -0.08 | +35.39 | 0.120 |
| digits_on/iid/dimret(k=0.3) | rho | 122612 | +6.56 | +6.55 | +0.011 ± 0.016 | +10.43 / +10.45 | +40.24 | +0.05 | +9.20 | 0.120 |
| digits_on/iid/dimret(k=0.3) | oracle_threshold | 106622 | +6.73 | +6.72 | +0.002 ± 0.018 | +11.41 / +11.44 | +35.86 | -0.06 | +18.09 | 0.120 |
| digits_on/iid/memory | rho | 141117 | +6.93 | +6.91 | +0.018 ± 0.018 | +11.63 / +11.61 | +48.91 | +0.13 | +17.72 | 0.252 |
| digits_on/iid/memory | oracle_threshold | 191629 | +6.80 | +6.79 | +0.002 ± 0.015 | +12.37 / +12.36 | +65.12 | -0.04 | +42.67 | 0.275 |
| digits_on/iid/memory_debiased | rho | 139844 | +6.47 | +6.45 | +0.015 ± 0.016 | +10.75 / +10.73 | +45.23 | +0.06 | +15.14 | 0.165 |
| digits_on/iid/memory_debiased | oracle_threshold | 193977 | +6.25 | +6.26 | -0.011 ± 0.015 | +11.40 / +11.40 | +60.57 | -0.08 | +40.40 | 0.228 |
| tabular_on/record/stationary | rho | 118085 | +9.41 | +9.40 | +0.012 ± 0.009 | +5.28 / +5.27 | +15.79 | -4.57 | +10.76 | 0.100 |
| tabular_on/record/stationary | oracle_threshold | 159291 | +8.93 | +8.92 | +0.007 ± 0.009 | +4.70 / +4.68 | +14.74 | -6.09 | +22.73 | 0.100 |
| tabular_on/record/dimret(k=0.3) | rho | 99320 | +9.21 | +9.20 | +0.015 ± 0.010 | +5.51 / +5.50 | +14.71 | -3.81 | +7.39 | 0.100 |
| tabular_on/record/dimret(k=0.3) | oracle_threshold | 82377 | +7.82 | +7.82 | +0.002 ± 0.012 | +6.13 / +6.10 | +11.89 | -3.18 | +12.40 | 0.100 |
| tabular_on/record/memory | rho | 119254 | +8.63 | +8.62 | +0.013 ± 0.011 | +5.76 / +5.75 | +14.33 | -7.58 | +17.73 | 0.239 |
| tabular_on/record/memory | oracle_threshold | 158444 | +8.94 | +8.94 | +0.003 ± 0.010 | +5.86 / +5.84 | +14.96 | -11.95 | +35.05 | 0.265 |
| tabular_on/record/memory_debiased | rho | 118347 | +9.16 | +9.14 | +0.013 ± 0.010 | +5.41 / +5.40 | +15.30 | -5.52 | +12.88 | 0.144 |
| tabular_on/record/memory_debiased | oracle_threshold | 158791 | +8.87 | +8.87 | -0.000 ± 0.009 | +5.41 / +5.39 | +14.85 | -9.88 | +30.56 | 0.207 |
| tabular_on/iid/stationary | rho | 154455 | +3.78 | +3.78 | +0.007 ± 0.009 | +5.92 / +5.91 | +29.21 | +0.01 | +9.61 | 0.100 |
| tabular_on/iid/stationary | oracle_threshold | 198114 | +3.27 | +3.26 | +0.010 ± 0.009 | +5.91 / +5.90 | +32.35 | +0.05 | +23.87 | 0.100 |
| tabular_on/iid/dimret(k=0.3) | rho | 133320 | +4.00 | +3.99 | +0.003 ± 0.010 | +6.13 / +6.12 | +26.64 | -0.01 | +6.46 | 0.100 |
| tabular_on/iid/dimret(k=0.3) | oracle_threshold | 103255 | +4.15 | +4.14 | +0.007 ± 0.012 | +7.20 / +7.18 | +21.42 | -0.01 | +13.07 | 0.100 |
| tabular_on/iid/memory | rho | 158446 | +4.06 | +4.06 | -0.003 ± 0.011 | +6.84 / +6.83 | +32.16 | +0.10 | +17.62 | 0.252 |
| tabular_on/iid/memory | oracle_threshold | 216051 | +4.08 | +4.08 | -0.000 ± 0.010 | +7.79 / +7.78 | +44.09 | -0.03 | +38.86 | 0.274 |
| tabular_on/iid/memory_debiased | rho | 156101 | +3.89 | +3.89 | -0.004 ± 0.010 | +6.27 / +6.26 | +30.35 | +0.03 | +12.70 | 0.160 |
| tabular_on/iid/memory_debiased | oracle_threshold | 211323 | +3.87 | +3.88 | -0.008 ± 0.009 | +7.29 / +7.28 | +40.88 | -0.03 | +34.84 | 0.228 |

Raw vs debiased display for the memory-reading proposer (W = 40):

| Scenario | noise | bold edits | policy | gain raw / debiased | debiased − raw gain | bold share raw / debiased |
|---|---|---|---|---|---|---|
| digits_on | record | as calibrated | rho | +19.95 / +17.03 | -2.92 ± 0.073 | 0.238 / 0.151 |
| digits_on | record | as calibrated | oracle_threshold | +37.95 / +36.02 | -1.93 ± 0.100 | 0.265 / 0.205 |
| digits_on | record | harmful bold | rho | +6.14 / +8.16 | +2.02 ± 0.061 | 0.214 / 0.136 |
| digits_on | record | harmful bold | oracle_threshold | +17.35 / +20.37 | +3.02 ± 0.073 | 0.236 / 0.176 |
| digits_on | iid | as calibrated | rho | +17.72 / +15.14 | -2.58 ± 0.080 | 0.252 / 0.165 |
| digits_on | iid | as calibrated | oracle_threshold | +42.67 / +40.40 | -2.27 ± 0.082 | 0.275 / 0.228 |
| digits_on | iid | harmful bold | rho | +1.49 / +4.87 | +3.38 ± 0.082 | 0.227 / 0.139 |
| digits_on | iid | harmful bold | oracle_threshold | +17.12 / +20.16 | +3.03 ± 0.072 | 0.245 / 0.187 |
| tabular_on | record | as calibrated | rho | +17.73 / +12.88 | -4.85 ± 0.068 | 0.239 / 0.144 |
| tabular_on | record | as calibrated | oracle_threshold | +35.05 / +30.56 | -4.49 ± 0.084 | 0.265 / 0.207 |
| tabular_on | record | harmful bold | rho | +3.25 / +4.22 | +0.97 ± 0.036 | 0.211 / 0.114 |
| tabular_on | record | harmful bold | oracle_threshold | +9.70 / +11.42 | +1.72 ± 0.043 | 0.229 / 0.152 |
| tabular_on | iid | as calibrated | rho | +17.62 / +12.70 | -4.92 ± 0.071 | 0.252 / 0.160 |
| tabular_on | iid | as calibrated | oracle_threshold | +38.86 / +34.84 | -4.02 ± 0.073 | 0.274 / 0.228 |
| tabular_on | iid | harmful bold | rho | +0.55 / +2.28 | +1.73 ± 0.049 | 0.226 / 0.117 |
| tabular_on | iid | harmful bold | oracle_threshold | +9.67 / +11.43 | +1.76 ± 0.043 | 0.240 / 0.165 |

## T6. Proposition 10: myopic vs lookahead threshold family (rules + oracle prior, no screening, N = W)

Lookahead family: t = t*_n + σ_d (θ0 + θ1 · remaining-budget fraction), (θ0, θ1) tuned on development campaigns.

| Node | W | case | best (θ0, θ1) | myopic gain | lookahead gain | lookahead − myopic (test, paired) | (δ_n) |
|---|---|---|---|---|---|---|---|
| digits_on | 20 | DI holds | (+0.4, -0.4) | +9.92 | +9.88 | -0.04 ± 0.012 | -0.02 |
| digits_on | 20 | diminishing returns k=0.3 | (+0.0, +0.0) | +7.91 | +7.91 | +0.00 ± 0.000 | +0.00 |
| digits_on | 20 | diminishing returns k=0.8 | (+0.0, -0.4) | +7.07 | +7.24 | +0.16 ± 0.012 | +0.08 |
| digits_on | 20 | memory-reading (raw B) | (+0.0, +0.0) | +10.83 | +10.83 | +0.00 ± 0.000 | +0.00 |
| digits_on | 20 | memory-reading (debiased B~) | (+0.4, -0.4) | +10.27 | +10.22 | -0.04 ± 0.014 | -0.02 |
| digits_on | 20 | record channel only | (-0.4, +0.4) | +9.79 | +9.89 | +0.09 ± 0.013 | +0.05 |
| digits_on | 20 | record + memory (raw B) | (-0.4, +0.4) | +10.51 | +10.69 | +0.18 ± 0.016 | +0.09 |
| digits_on | 20 | record + memory (debiased B~) | (-0.4, +0.4) | +10.05 | +10.16 | +0.11 ± 0.014 | +0.06 |
| digits_on | 40 | DI holds | (+0.0, +0.0) | +19.72 | +19.72 | +0.00 ± 0.000 | +0.00 |
| digits_on | 40 | diminishing returns k=0.3 | (+0.2, -0.4) | +12.86 | +12.90 | +0.04 ± 0.011 | +0.02 |
| digits_on | 40 | diminishing returns k=0.8 | (+0.0, -0.4) | +10.12 | +10.41 | +0.29 ± 0.014 | +0.15 |
| digits_on | 40 | memory-reading (raw B) | (+0.0, +0.0) | +22.85 | +22.85 | +0.00 ± 0.000 | +0.00 |
| digits_on | 40 | memory-reading (debiased B~) | (+0.0, +0.0) | +21.31 | +21.31 | +0.00 ± 0.000 | +0.00 |
| digits_on | 40 | record channel only | (-0.4, +0.4) | +19.16 | +19.56 | +0.40 ± 0.018 | +0.20 |
| digits_on | 40 | record + memory (raw B) | (-0.4, +0.0) | +21.25 | +22.33 | +1.08 ± 0.047 | +0.54 |
| digits_on | 40 | record + memory (debiased B~) | (-0.4, +0.4) | +20.06 | +20.58 | +0.53 ± 0.021 | +0.26 |
| tabular_on | 20 | DI holds | (+0.0, +0.0) | +6.62 | +6.62 | +0.00 ± 0.000 | +0.00 |
| tabular_on | 20 | diminishing returns k=0.3 | (-0.4, +0.4) | +5.41 | +5.40 | -0.01 ± 0.007 | -0.00 |
| tabular_on | 20 | diminishing returns k=0.8 | (+0.0, -0.4) | +4.93 | +5.05 | +0.12 ± 0.008 | +0.06 |
| tabular_on | 20 | memory-reading (raw B) | (+0.0, +0.0) | +8.56 | +8.56 | +0.00 ± 0.000 | +0.00 |
| tabular_on | 20 | memory-reading (debiased B~) | (+0.0, +0.0) | +7.43 | +7.43 | +0.00 ± 0.000 | +0.00 |
| tabular_on | 20 | record channel only | (-0.4, +0.4) | +6.55 | +6.61 | +0.06 ± 0.008 | +0.03 |
| tabular_on | 20 | record + memory (raw B) | (-0.4, +0.4) | +8.29 | +8.41 | +0.12 ± 0.011 | +0.06 |
| tabular_on | 20 | record + memory (debiased B~) | (-0.4, +0.4) | +7.21 | +7.30 | +0.09 ± 0.009 | +0.04 |
| tabular_on | 40 | DI holds | (+0.0, +0.0) | +13.22 | +13.22 | +0.00 ± 0.000 | +0.00 |
| tabular_on | 40 | diminishing returns k=0.3 | (+0.2, -0.4) | +9.00 | +9.05 | +0.05 ± 0.007 | +0.03 |
| tabular_on | 40 | diminishing returns k=0.8 | (-0.4, -0.4) | +7.35 | +7.49 | +0.14 ± 0.013 | +0.07 |
| tabular_on | 40 | memory-reading (raw B) | (+0.2, -0.4) | +19.59 | +19.64 | +0.05 ± 0.018 | +0.02 |
| tabular_on | 40 | memory-reading (debiased B~) | (+0.0, +0.0) | +16.75 | +16.75 | +0.00 ± 0.000 | +0.00 |
| tabular_on | 40 | record channel only | (-0.2, +0.0) | +12.89 | +13.13 | +0.23 ± 0.016 | +0.12 |
| tabular_on | 40 | record + memory (raw B) | (-0.4, +0.0) | +18.27 | +19.19 | +0.92 ± 0.034 | +0.46 |
| tabular_on | 40 | record + memory (debiased B~) | (-0.4, +0.4) | +15.52 | +15.85 | +0.33 ± 0.015 | +0.16 |

## T7. DI-test artefact and value-proxy selection bias (E1b-style forks, W = 20, points 4/8/12, verify r = 2, rule ρ, DI-satisfying stationary proposer unless 'feedback' ≠ 0)

Outcomes of the next 1 / 3 trials: Δ̂ (relative to the branch's recorded incumbent), abs (recorded metric of the candidate), tv (true value J of the candidate), ti (true increment over the branch's own incumbent, i.e. an audited increment). For the next trial, Δ̂ shift = abs shift − record shift exactly.

**T7a. Signed shifts, verify − continue, at changed points (repetitions averaged)**

| Study | split | ϱ | feedback | P(prom) / P(dem) | record shift | Δ̂ 1 / 3 | abs 1 / 3 | tv 1 / 3 | ti 1 / 3 |
|---|---|---|---|---|---|---|---|---|---|
| tabular/hom | fixed | 0.0 | +0.0 σ_d | 0.079 / 0.040 | -2.25 | +2.50 / +1.91 | +0.25 / +0.24 | +0.30 / +0.29 | -0.01 / -0.00 |
| tabular/hom | fixed | 0.5 | +0.0 σ_d | 0.076 / 0.050 | -2.20 | +1.18 / +1.05 | -1.01 / -0.85 | +0.26 / +0.25 | -0.01 / -0.00 |
| tabular/hom | fixed | 0.8 | +0.0 σ_d | 0.077 / 0.060 | -2.30 | +0.64 / +0.59 | -1.65 / -1.52 | +0.30 / +0.28 | -0.00 / -0.01 |
| tabular/hom | vary | 0.0 | +0.0 σ_d | 0.187 / 0.057 | -4.28 | +4.52 / +3.42 | +0.24 / +0.22 | +0.38 / +0.33 | -0.01 / +0.00 |
| tabular/hom | vary | 0.5 | +0.0 σ_d | 0.166 / 0.077 | -4.05 | +2.20 / +1.93 | -1.85 / -1.58 | +0.46 / +0.45 | +0.00 / +0.01 |
| tabular/hom | vary | 0.8 | +0.0 σ_d | 0.158 / 0.102 | -4.19 | +1.18 / +1.08 | -3.02 / -2.79 | +0.56 / +0.53 | -0.00 / -0.01 |
| tabular/nearnull | fixed | 0.0 | +0.0 σ_d | 0.082 / 0.063 | -1.02 | +0.56 / +0.49 | -0.45 / -0.38 | +0.15 / +0.14 | -0.00 / +0.00 |
| tabular/nearnull | fixed | 0.5 | +0.0 σ_d | 0.087 / 0.076 | -0.96 | +0.26 / +0.26 | -0.70 / -0.64 | +0.11 / +0.12 | -0.01 / +0.01 |
| tabular/nearnull | fixed | 0.8 | +0.0 σ_d | 0.094 / 0.087 | -1.10 | +0.12 / +0.14 | -0.97 / -0.92 | +0.10 / +0.11 | -0.02 / -0.00 |
| tabular/nearnull | vary | 0.0 | +0.0 σ_d | 0.168 / 0.111 | -1.92 | +1.03 / +0.89 | -0.89 / -0.75 | +0.21 / +0.20 | -0.00 / +0.01 |
| tabular/nearnull | vary | 0.5 | +0.0 σ_d | 0.172 / 0.135 | -1.76 | +0.49 / +0.45 | -1.27 / -1.17 | +0.21 / +0.20 | +0.01 / -0.00 |
| tabular/nearnull | vary | 0.8 | +0.0 σ_d | 0.182 / 0.160 | -1.88 | +0.26 / +0.25 | -1.62 / -1.55 | +0.28 / +0.27 | -0.00 / +0.00 |
| digits/hom | fixed | 0.0 | +0.0 σ_d | 0.086 / 0.044 | -3.44 | +4.47 / +3.28 | +1.03 / +1.22 | +1.14 / +1.31 | +0.00 / +0.01 |
| digits/hom | fixed | 0.5 | +0.0 σ_d | 0.082 / 0.050 | -3.40 | +2.12 / +1.83 | -1.29 / -0.90 | +0.95 / +1.05 | -0.03 / -0.01 |
| digits/hom | fixed | 0.8 | +0.0 σ_d | 0.080 / 0.060 | -3.67 | +1.09 / +1.00 | -2.59 / -2.30 | +0.76 / +0.77 | +0.01 / +0.01 |
| digits/hom | vary | 0.0 | +0.0 σ_d | 0.202 / 0.061 | -6.50 | +7.78 / +5.67 | +1.28 / +1.61 | +1.52 / +1.78 | -0.02 / -0.03 |
| digits/hom | vary | 0.5 | +0.0 σ_d | 0.184 / 0.077 | -6.32 | +3.77 / +3.24 | -2.54 / -1.84 | +1.45 / +1.61 | +0.00 / +0.01 |
| digits/hom | vary | 0.8 | +0.0 σ_d | 0.166 / 0.098 | -6.72 | +1.97 / +1.80 | -4.75 / -4.26 | +1.30 / +1.32 | -0.01 / -0.02 |
| digits/nearnull | fixed | 0.5 | +0.0 σ_d | 0.093 / 0.080 | -1.50 | +0.45 / +0.40 | -1.06 / -0.95 | +0.33 / +0.34 | +0.01 / -0.00 |
| tabular/nearnull | fixed | 0.5 | +0.5 σ_d | 0.087 / 0.076 | -1.00 | +0.43 / +0.41 | -0.57 / -0.41 | +0.29 / +0.38 | +0.17 / +0.16 |
| digits/hom | fixed | 0.5 | +0.5 σ_d | 0.079 / 0.051 | -3.41 | +2.89 / +2.57 | -0.52 / +0.30 | +1.72 / +2.19 | +0.80 / +0.79 |
| tabular/hom ×0.5 noise | fixed | 0.5 | +0.0 σ_d | 0.048 / 0.035 | -1.06 | +0.68 / +0.57 | -0.38 / -0.31 | +0.29 / +0.29 | +0.01 / -0.00 |
| tabular/hom ×2 noise | fixed | 0.5 | +0.0 σ_d | 0.101 / 0.058 | -4.45 | +2.18 / +1.91 | -2.26 / -2.05 | +0.06 / +0.00 | -0.01 / -0.01 |

**T7b. Distance criterion: excess of the changed-point cross-action distance over the paired same-action null (population), abs next-1 distances (observed tabular memory-on: D_changed 2.31, D_null 1.08, D_unchanged 0.55; digits memory-off 6.04 / 4.64 / 1.97), and the rate at which small studies (18 tabular / 6 digits instances × 3 points) meet the simplified combined criterion**

| Study | split | ϱ | feedback | abs next-1 D_ch / D_null / D_unch | excess Δ̂ 1 / 3 | abs 1 / 3 | tv 1 / 3 | ti 1 / 3 | flag rate Δ̂ 1/3 · abs 1/3 · tv 1/3 · ti 1/3 |
|---|---|---|---|---|---|---|---|---|---|
| tabular/hom | fixed | 0.0 | +0.0 σ_d | 2.94 / 0.74 / 0.73 | +3.02 / +2.17 | +2.20 / +2.01 | +2.22 / +2.07 | -0.00 / -0.00 | 0.78 0.86 · 0.62 0.77 · 0.70 0.81 · 0.00 0.00 |
| tabular/hom | fixed | 0.5 | +0.0 σ_d | 2.32 / 0.81 / 0.78 | +1.44 / +1.13 | +1.51 / +1.38 | +2.21 / +2.07 | -0.00 / -0.00 | 0.38 0.59 · 0.40 0.58 · 0.71 0.82 · 0.00 0.00 |
| tabular/hom | fixed | 0.8 | +0.0 σ_d | 2.57 / 0.83 / 0.82 | +0.81 / +0.64 | +1.74 / +1.51 | +2.50 / +2.34 | -0.00 / -0.00 | 0.18 0.26 · 0.46 0.60 · 0.79 0.90 · 0.00 0.00 |
| tabular/hom | vary | 0.0 | +0.0 σ_d | 2.79 / 0.76 / 0.73 | +4.36 / +3.13 | +2.03 / +1.89 | +1.99 / +1.92 | -0.00 / -0.00 | 0.99 1.00 · 0.81 0.93 · 0.87 0.95 · 0.00 0.00 |
| tabular/hom | vary | 0.5 | +0.0 σ_d | 2.94 / 0.77 / 0.76 | +2.10 / +1.65 | +2.17 / +1.88 | +2.00 / +1.87 | +0.01 / -0.00 | 0.82 0.96 · 0.82 0.92 · 0.87 0.95 · 0.00 0.00 |
| tabular/hom | vary | 0.8 | +0.0 σ_d | 3.75 / 0.81 / 0.82 | +1.11 / +0.89 | +2.94 / +2.57 | +2.20 / +2.07 | -0.00 / +0.00 | 0.41 0.63 · 0.92 0.96 · 0.89 0.96 · 0.00 0.00 |
| tabular/nearnull | fixed | 0.0 | +0.0 σ_d | 1.49 / 0.51 / 0.55 | +0.70 / +0.55 | +0.98 / +0.77 | +1.04 / +0.99 | +0.00 / +0.00 | 0.22 0.28 · 0.33 0.37 · 0.46 0.55 · 0.00 0.00 |
| tabular/nearnull | fixed | 0.5 | +0.0 σ_d | 1.30 / 0.53 / 0.54 | +0.31 / +0.25 | +0.77 / +0.66 | +0.98 / +0.91 | -0.01 / -0.01 | 0.11 0.11 · 0.28 0.32 · 0.46 0.54 · 0.00 0.00 |
| tabular/nearnull | fixed | 0.8 | +0.0 σ_d | 1.49 / 0.57 / 0.55 | +0.19 / +0.16 | +0.92 / +0.81 | +1.11 / +1.05 | +0.00 / -0.00 | 0.09 0.08 · 0.36 0.40 · 0.55 0.64 · 0.00 0.00 |
| tabular/nearnull | vary | 0.0 | +0.0 σ_d | 1.91 / 0.52 / 0.54 | +0.98 / +0.79 | +1.38 / +1.07 | +0.97 / +0.94 | -0.00 / -0.00 | 0.42 0.63 · 0.63 0.70 · 0.59 0.74 · 0.00 0.00 |
| tabular/nearnull | vary | 0.5 | +0.0 σ_d | 1.83 / 0.52 / 0.54 | +0.47 / +0.39 | +1.30 / +1.13 | +0.92 / +0.87 | -0.00 / -0.00 | 0.22 0.33 · 0.63 0.73 · 0.60 0.70 · 0.00 0.00 |
| tabular/nearnull | vary | 0.8 | +0.0 σ_d | 2.11 / 0.57 / 0.56 | +0.25 / +0.21 | +1.54 / +1.38 | +0.98 / +0.93 | -0.00 / -0.00 | 0.13 0.14 · 0.72 0.81 · 0.62 0.73 · 0.00 0.00 |
| digits/hom | fixed | 0.0 | +0.0 σ_d | 5.37 / 1.26 / 1.27 | +5.44 / +3.73 | +4.11 / +3.91 | +4.16 / +4.03 | +0.00 / -0.00 | 0.45 0.45 · 0.37 0.41 · 0.41 0.46 · 0.00 0.00 |
| digits/hom | fixed | 0.5 | +0.0 σ_d | 3.75 / 1.31 / 1.30 | +2.57 / +1.95 | +2.44 / +2.33 | +4.03 / +3.81 | -0.01 / +0.00 | 0.24 0.24 · 0.23 0.22 · 0.41 0.44 · 0.00 0.00 |
| digits/hom | fixed | 0.8 | +0.0 σ_d | 4.17 / 1.43 / 1.40 | +1.35 / +1.07 | +2.74 / +2.35 | +4.31 / +3.99 | +0.01 / +0.01 | 0.16 0.10 · 0.25 0.21 · 0.44 0.46 · 0.00 0.00 |
| digits/hom | vary | 0.0 | +0.0 σ_d | 4.93 / 1.24 / 1.24 | +7.54 / +5.16 | +3.69 / +3.54 | +3.64 / +3.63 | -0.01 / +0.00 | 0.80 0.81 · 0.53 0.59 · 0.57 0.64 · 0.00 0.00 |
| digits/hom | vary | 0.5 | +0.0 σ_d | 4.63 / 1.30 / 1.29 | +3.60 / +2.79 | +3.34 / +2.84 | +3.62 / +3.46 | -0.00 / -0.00 | 0.51 0.60 · 0.46 0.46 · 0.57 0.63 · 0.00 0.00 |
| digits/hom | vary | 0.8 | +0.0 σ_d | 6.06 / 1.39 / 1.43 | +1.87 / +1.50 | +4.67 / +3.93 | +3.83 / +3.56 | -0.01 / -0.00 | 0.29 0.28 · 0.55 0.54 · 0.59 0.63 · 0.00 0.00 |
| digits/nearnull | fixed | 0.5 | +0.0 σ_d | 2.13 / 0.87 / 0.88 | +0.54 / +0.45 | +1.25 / +1.05 | +1.72 / +1.63 | +0.00 / +0.00 | 0.16 0.08 · 0.25 0.14 · 0.33 0.25 · 0.00 0.00 |
| tabular/nearnull | fixed | 0.5 | +0.5 σ_d | 2.68 / 0.53 / 0.53 | +2.12 / +1.95 | +2.14 / +3.03 | +2.35 / +3.35 | +2.07 / +1.94 | 0.84 0.99 · 0.83 0.99 · 0.92 0.99 · 0.92 1.00 |
| digits/hom | fixed | 0.5 | +0.5 σ_d | 5.47 / 1.35 / 1.31 | +4.75 / +4.21 | +4.12 / +5.13 | +5.88 / +6.82 | +3.34 / +2.96 | 0.39 0.55 · 0.35 0.51 · 0.53 0.62 · 0.34 0.53 |
| tabular/hom ×0.5 noise | fixed | 0.5 | +0.0 σ_d | 1.51 / 0.67 / 0.65 | +0.84 / +0.63 | +0.85 / +0.78 | +1.39 / +1.25 | +0.00 / +0.00 | 0.17 0.21 · 0.16 0.20 · 0.33 0.41 · 0.00 0.00 |
| tabular/hom ×2 noise | fixed | 0.5 | +0.0 σ_d | 3.81 / 1.09 / 1.09 | +2.45 / +1.93 | +2.72 / +2.42 | +3.11 / +2.95 | +0.00 / -0.00 | 0.55 0.80 · 0.62 0.80 · 0.91 0.96 · 0.00 0.00 |

Value residual = audited Y difference − immediate proxy (+D̄ for a promotion, −D̄ for a demotion) − unchanged-point budget correction, averaged over changed points. Observed (19 Oct, memory-on tabular, fixed split): P(prom) 0.167, P(dem) 0.074, E[D̄ | prom] +0.44, E[−D̄ | dem] +1.70, proxy +0.83, residual −1.22 [−2.22, −0.26] (10⁻³).

| Study | split | ϱ | feedback | E[D̄ \| prom] | E[Δ \| prom] | E[−D̄ \| dem] | immediate proxy | true immediate | proxy bias | continuation part | **expected residual** | proxy bias / proxy | small studies: mean, sd, [5 %, 95 %], P(≤ −1.22) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| tabular/hom | fixed | 0.0 | +0.0 | +1.93 | +0.56 | +2.00 | +1.95 | +0.31 | +1.64 | +0.01 | **-1.64** | 0.84 | -1.69, 3.05, [-6.54, +2.78], 0.54 |
| tabular/hom | fixed | 0.5 | +0.0 | +1.93 | +0.22 | +2.01 | +1.96 | +0.27 | +1.69 | -0.03 | **-1.72** | 0.86 | -1.70, 2.81, [-6.50, +2.75], 0.57 |
| tabular/hom | fixed | 0.8 | +0.0 | +2.08 | -0.10 | +2.23 | +2.15 | +0.30 | +1.85 | -0.04 | **-1.88** | 0.86 | -1.88, 2.74, [-6.45, +2.09], 0.58 |
| tabular/hom | vary | 0.0 | +0.0 | +2.96 | +0.34 | +3.04 | +2.98 | +0.39 | +2.59 | +0.13 | **-2.47** | 0.87 | -2.49, 2.00, [-5.99, +0.61], 0.74 |
| tabular/hom | vary | 0.5 | +0.0 | +2.95 | +0.26 | +3.25 | +3.04 | +0.46 | +2.58 | +0.07 | **-2.51** | 0.85 | -2.51, 1.95, [-5.75, +0.61], 0.75 |
| tabular/hom | vary | 0.8 | +0.0 | +3.20 | +0.18 | +3.53 | +3.33 | +0.56 | +2.77 | -0.00 | **-2.77** | 0.83 | -2.77, 1.90, [-5.91, +0.26], 0.79 |
| tabular/nearnull | fixed | 0.0 | +0.0 | +0.98 | +0.17 | +0.81 | +0.91 | +0.15 | +0.76 | -0.06 | **-0.82** | 0.83 | -0.83, 1.81, [-4.08, +1.98], 0.39 |
| tabular/nearnull | fixed | 0.5 | +0.0 | +0.90 | -0.02 | +0.87 | +0.89 | +0.12 | +0.77 | -0.02 | **-0.79** | 0.87 | -0.78, 1.65, [-3.48, +1.71], 0.37 |
| tabular/nearnull | fixed | 0.8 | +0.0 | +1.04 | -0.13 | +1.03 | +1.04 | +0.12 | +0.92 | +0.03 | **-0.88** | 0.88 | -0.88, 1.65, [-3.66, +1.67], 0.40 |
| tabular/nearnull | vary | 0.0 | +0.0 | +1.64 | +0.18 | +1.15 | +1.45 | +0.21 | +1.23 | -0.06 | **-1.29** | 0.85 | -1.29, 1.37, [-3.63, +0.77], 0.50 |
| tabular/nearnull | vary | 0.5 | +0.0 | +1.43 | +0.08 | +1.29 | +1.37 | +0.21 | +1.16 | -0.02 | **-1.18** | 0.85 | -1.19, 1.24, [-3.37, +0.82], 0.47 |
| tabular/nearnull | vary | 0.8 | +0.0 | +1.52 | +0.09 | +1.57 | +1.55 | +0.28 | +1.27 | -0.03 | **-1.30** | 0.82 | -1.28, 1.24, [-3.29, +0.70], 0.51 |
| digits/hom | fixed | 0.0 | +0.0 | +3.34 | +2.63 | +3.05 | +3.24 | +1.14 | +2.10 | +0.87 | **-1.23** | 0.65 | -1.14, 9.49, [-16.80, +13.90], 0.50 |
| digits/hom | fixed | 0.5 | +0.0 | +3.32 | +2.11 | +3.11 | +3.24 | +0.99 | +2.26 | +0.63 | **-1.63** | 0.70 | -1.59, 9.03, [-16.45, +12.92], 0.51 |
| digits/hom | fixed | 0.8 | +0.0 | +3.52 | +1.51 | +3.47 | +3.50 | +0.75 | +2.75 | +0.34 | **-2.41** | 0.78 | -2.27, 8.68, [-16.16, +11.23], 0.55 |
| digits/hom | vary | 0.0 | +0.0 | +5.67 | +2.14 | +4.47 | +5.39 | +1.54 | +3.85 | +1.71 | **-2.14** | 0.71 | -2.28, 6.96, [-13.59, +8.83], 0.56 |
| digits/hom | vary | 0.5 | +0.0 | +5.53 | +1.98 | +4.75 | +5.30 | +1.44 | +3.86 | +1.06 | **-2.80** | 0.73 | -2.83, 6.58, [-13.58, +7.80], 0.61 |
| digits/hom | vary | 0.8 | +0.0 | +5.87 | +1.72 | +5.39 | +5.70 | +1.31 | +4.38 | +0.35 | **-4.03** | 0.77 | -4.08, 6.46, [-14.83, +6.10], 0.68 |
| digits/nearnull | fixed | 0.5 | +0.0 | +1.57 | +0.74 | +1.31 | +1.45 | +0.32 | +1.13 | +0.20 | **-0.93** | 0.78 | -0.94, 5.61, [-9.90, +7.45], 0.45 |
| tabular/nearnull | fixed | 0.5 | +0.5 | +0.92 | -0.01 | +0.88 | +0.90 | +0.12 | +0.77 | +0.31 | **-0.46** | 0.86 | -0.48, 2.44, [-4.59, +3.33], 0.38 |
| digits/hom | fixed | 0.5 | +0.5 | +3.29 | +2.14 | +3.18 | +3.24 | +0.92 | +2.33 | +1.94 | **-0.39** | 0.72 | -0.22, 10.86, [-17.99, +17.01], 0.45 |
| tabular/hom ×0.5 noise | fixed | 0.5 | +0.0 | +1.02 | +0.33 | +1.04 | +1.03 | +0.29 | +0.74 | -0.01 | **-0.75** | 0.72 | -0.72, 3.12, [-6.38, +3.81], 0.38 |
| tabular/hom ×2 noise | fixed | 0.5 | +0.0 | +3.68 | -0.45 | +4.13 | +3.84 | +0.07 | +3.77 | -0.18 | **-3.95** | 0.98 | -3.97, 2.70, [-8.52, +0.32], 0.86 |

## T8. Headroom map: oracle-prior control (threshold + screening) − A2+screen, in δ_n per campaign (iid noise, stationary proposer, N = 2W)

**digits_on, W = 20** (columns: dispersion multiplier, with sd of type means / σ_d; ≥ 1.00 means the oracle clears δ_n)

| inert share | ×0 (0.00) | ×0.5 (0.36) | ×1 (0.71) | ×1.5 (1.07) | ×2 (1.42) | ×3 (2.14) |
|---|---|---|---|---|---|---|
| 0.20 | +3.82 | +2.41 | +5.82 | +11.54 | +12.97 | +16.23 |
| 0.40 | +2.04 | +0.73 | +3.22 | +6.64 | +7.39 | +5.47 |
| 0.55 | +0.97 | +0.54 | +1.54 | +3.21 | +3.39 | +2.45 |
| 0.70 | +0.69 | +0.35 | +0.93 | +1.89 | +1.88 | +0.88 |

**digits_on, W = 40** (columns: dispersion multiplier, with sd of type means / σ_d; ≥ 1.00 means the oracle clears δ_n)

| inert share | ×0 (0.00) | ×0.5 (0.36) | ×1 (0.71) | ×1.5 (1.07) | ×2 (1.42) | ×3 (2.14) |
|---|---|---|---|---|---|---|
| 0.20 | +7.86 | +4.63 | +11.77 | +22.91 | +26.44 | +32.02 |
| 0.40 | +4.02 | +1.32 | +6.39 | +13.21 | +14.00 | +9.28 |
| 0.55 | +1.97 | +1.14 | +2.84 | +6.01 | +6.03 | +3.54 |
| 0.70 | +1.34 | +0.79 | +1.90 | +3.77 | +3.72 | +1.72 |

**digits_on, W = 20, one within-type τ, all edits local** (columns: dispersion multiplier, with sd of type means / σ_d; ≥ 1.00 means the oracle clears δ_n)

| inert share | ×0 (0.00) | ×0.5 (0.36) | ×1 (0.71) | ×1.5 (1.07) | ×2 (1.42) | ×3 (2.14) |
|---|---|---|---|---|---|---|
| 0.20 | +0.00 | +2.39 | +6.04 | +11.55 | +17.61 | +29.70 |
| 0.40 | -0.01 | +0.63 | +2.84 | +5.22 | +7.54 | +11.29 |
| 0.55 | -0.00 | +0.27 | +0.79 | +1.81 | +2.52 | +2.46 |
| 0.70 | -0.01 | +0.14 | +0.56 | +1.02 | +1.24 | +1.06 |

**tabular_on, W = 20** (columns: dispersion multiplier, with sd of type means / σ_d; ≥ 1.00 means the oracle clears δ_n)

| inert share | ×0 (0.00) | ×0.5 (0.27) | ×1 (0.54) | ×1.5 (0.81) | ×2 (1.08) | ×3 (1.62) |
|---|---|---|---|---|---|---|
| 0.20 | +3.57 | +2.36 | +4.05 | +7.07 | +9.80 | +13.78 |
| 0.40 | +1.72 | +1.36 | +1.83 | +3.51 | +4.66 | +5.42 |
| 0.55 | +0.82 | +0.58 | +0.93 | +1.72 | +2.05 | +1.81 |
| 0.70 | +0.57 | +0.37 | +0.62 | +1.17 | +1.35 | +0.89 |

**tabular_on, W = 40** (columns: dispersion multiplier, with sd of type means / σ_d; ≥ 1.00 means the oracle clears δ_n)

| inert share | ×0 (0.00) | ×0.5 (0.27) | ×1 (0.54) | ×1.5 (0.81) | ×2 (1.08) | ×3 (1.62) |
|---|---|---|---|---|---|---|
| 0.20 | +7.21 | +5.10 | +8.12 | +14.19 | +19.58 | +27.43 |
| 0.40 | +3.51 | +2.83 | +3.72 | +7.01 | +9.28 | +11.42 |
| 0.55 | +1.66 | +1.13 | +1.83 | +3.40 | +4.00 | +3.11 |
| 0.70 | +1.11 | +0.75 | +1.25 | +2.28 | +2.69 | +1.78 |

**tabular_on, W = 20, one within-type τ, all edits local** (columns: dispersion multiplier, with sd of type means / σ_d; ≥ 1.00 means the oracle clears δ_n)

| inert share | ×0 (0.00) | ×0.5 (0.27) | ×1 (0.54) | ×1.5 (0.81) | ×2 (1.08) | ×3 (1.62) |
|---|---|---|---|---|---|---|
| 0.20 | +0.00 | +1.35 | +3.44 | +5.96 | +8.68 | +13.91 |
| 0.40 | -0.00 | +0.31 | +1.45 | +2.57 | +3.62 | +5.57 |
| 0.55 | +0.00 | +0.07 | +0.34 | +0.76 | +1.20 | +1.53 |
| 0.70 | +0.00 | +0.06 | +0.25 | +0.45 | +0.64 | +0.67 |

## T9. Gain vs predictor quality (screening g tuned per predictor; contrast vs A2+screen, paired)

| Scenario | W | predictor | gain | vs A2+screen | (δ_n) |
|---|---|---|---|---|---|
| digits_on/iid/stationary | 20 | calibrated, noise 0 sd_types | +19.21 | +4.87 ± 0.073 | +2.44 |
| digits_on/iid/stationary | 20 | calibrated, noise 0.25 sd_types | +18.78 | +4.44 ± 0.071 | +2.22 |
| digits_on/iid/stationary | 20 | calibrated, noise 0.5 sd_types | +17.90 | +3.56 ± 0.065 | +1.78 |
| digits_on/iid/stationary | 20 | calibrated, noise 1 sd_types | +16.19 | +1.86 ± 0.063 | +0.93 |
| digits_on/iid/stationary | 20 | calibrated, noise 2 sd_types | +14.66 | +0.32 ± 0.048 | +0.16 |
| digits_on/iid/stationary | 20 | calibrated, noise 4 sd_types | +14.42 | +0.08 ± 0.025 | +0.04 |
| digits_on/iid/stationary | 20 | raw (uncalibrated), noise 0.5 sd_types | +17.61 | +3.27 ± 0.074 | +1.63 |
| digits_on/iid/stationary | 20 | raw (uncalibrated), noise 1 sd_types | +14.42 | +0.08 ± 0.081 | +0.04 |
| digits_on/iid/stationary | 20 | raw (uncalibrated), noise 2 sd_types | +8.01 | -6.33 ± 0.085 | -3.16 |
| digits_on/iid/stationary | 20 | mu_hat dispersion x0 | +9.28 | -5.06 ± 0.068 | -2.53 |
| digits_on/iid/stationary | 20 | mu_hat dispersion x0.5 | +15.28 | +0.95 ± 0.070 | +0.47 |
| digits_on/iid/stationary | 20 | mu_hat dispersion x1.5 | +18.01 | +3.68 ± 0.076 | +1.84 |
| digits_on/iid/stationary | 20 | mu_hat dispersion x2 | +17.03 | +2.70 ± 0.078 | +1.35 |
| digits_on/iid/stationary | 20 | tau_hat x0.5 | +11.48 | -2.85 ± 0.089 | -1.43 |
| digits_on/iid/stationary | 20 | tau_hat x2 | +17.75 | +3.41 ± 0.079 | +1.71 |
| digits_on/record/stationary | 20 | calibrated, noise 0 sd_types | +18.91 | +5.52 ± 0.073 | +2.76 |
| digits_on/record/stationary | 20 | calibrated, noise 0.25 sd_types | +18.38 | +4.98 ± 0.070 | +2.49 |
| digits_on/record/stationary | 20 | calibrated, noise 0.5 sd_types | +17.27 | +3.88 ± 0.063 | +1.94 |
| digits_on/record/stationary | 20 | calibrated, noise 1 sd_types | +15.51 | +2.12 ± 0.061 | +1.06 |
| digits_on/record/stationary | 20 | calibrated, noise 2 sd_types | +13.97 | +0.58 ± 0.047 | +0.29 |
| digits_on/record/stationary | 20 | calibrated, noise 4 sd_types | +13.52 | +0.13 ± 0.027 | +0.06 |
| digits_on/record/stationary | 20 | raw (uncalibrated), noise 0.5 sd_types | +17.48 | +4.09 ± 0.075 | +2.04 |
| digits_on/record/stationary | 20 | raw (uncalibrated), noise 1 sd_types | +14.72 | +1.33 ± 0.081 | +0.66 |
| digits_on/record/stationary | 20 | raw (uncalibrated), noise 2 sd_types | +8.84 | -4.55 ± 0.086 | -2.27 |
| digits_on/record/stationary | 20 | mu_hat dispersion x0 | +8.71 | -4.68 ± 0.067 | -2.34 |
| digits_on/record/stationary | 20 | mu_hat dispersion x0.5 | +14.13 | +0.73 ± 0.068 | +0.37 |
| digits_on/record/stationary | 20 | mu_hat dispersion x1.5 | +18.24 | +4.85 ± 0.080 | +2.42 |
| digits_on/record/stationary | 20 | mu_hat dispersion x2 | +17.26 | +3.87 ± 0.082 | +1.94 |
| digits_on/record/stationary | 20 | tau_hat x0.5 | +11.55 | -1.84 ± 0.084 | -0.92 |
| digits_on/record/stationary | 20 | tau_hat x2 | +18.33 | +4.93 ± 0.075 | +2.47 |
| digits_on/iid/stationary | 40 | calibrated, noise 0 sd_types | +38.64 | +9.50 ± 0.102 | +4.75 |
| digits_on/iid/stationary | 40 | calibrated, noise 0.25 sd_types | +37.74 | +8.59 ± 0.099 | +4.30 |
| digits_on/iid/stationary | 40 | calibrated, noise 0.5 sd_types | +36.36 | +7.22 ± 0.092 | +3.61 |
| digits_on/iid/stationary | 40 | calibrated, noise 1 sd_types | +32.99 | +3.84 ± 0.090 | +1.92 |
| digits_on/iid/stationary | 40 | calibrated, noise 2 sd_types | +30.20 | +1.05 ± 0.069 | +0.53 |
| digits_on/iid/stationary | 40 | calibrated, noise 4 sd_types | +29.36 | +0.22 ± 0.036 | +0.11 |
| digits_on/iid/stationary | 40 | raw (uncalibrated), noise 0.5 sd_types | +35.43 | +6.29 ± 0.103 | +3.14 |
| digits_on/iid/stationary | 40 | raw (uncalibrated), noise 1 sd_types | +29.00 | -0.15 ± 0.113 | -0.07 |
| digits_on/iid/stationary | 40 | raw (uncalibrated), noise 2 sd_types | +16.35 | -12.80 ± 0.122 | -6.40 |
| digits_on/iid/stationary | 40 | mu_hat dispersion x0 | +18.66 | -10.49 ± 0.097 | -5.24 |
| digits_on/iid/stationary | 40 | mu_hat dispersion x0.5 | +30.44 | +1.30 ± 0.098 | +0.65 |
| digits_on/iid/stationary | 40 | mu_hat dispersion x1.5 | +36.16 | +7.01 ± 0.107 | +3.51 |
| digits_on/iid/stationary | 40 | mu_hat dispersion x2 | +34.16 | +5.02 ± 0.109 | +2.51 |
| digits_on/iid/stationary | 40 | tau_hat x0.5 | +23.48 | -5.66 ± 0.126 | -2.83 |
| digits_on/iid/stationary | 40 | tau_hat x2 | +35.86 | +6.72 ± 0.112 | +3.36 |
| tabular_on/iid/stationary | 20 | calibrated, noise 0 sd_types | +12.40 | +2.73 ± 0.051 | +1.36 |
| tabular_on/iid/stationary | 20 | calibrated, noise 0.25 sd_types | +12.58 | +2.91 ± 0.047 | +1.45 |
| tabular_on/iid/stationary | 20 | calibrated, noise 0.5 sd_types | +12.03 | +2.36 ± 0.046 | +1.18 |
| tabular_on/iid/stationary | 20 | calibrated, noise 1 sd_types | +11.20 | +1.53 ± 0.043 | +0.76 |
| tabular_on/iid/stationary | 20 | calibrated, noise 2 sd_types | +10.13 | +0.45 ± 0.031 | +0.23 |
| tabular_on/iid/stationary | 20 | calibrated, noise 4 sd_types | +9.74 | +0.07 ± 0.015 | +0.03 |
| tabular_on/iid/stationary | 20 | raw (uncalibrated), noise 0.5 sd_types | +12.12 | +2.44 ± 0.049 | +1.22 |
| tabular_on/iid/stationary | 20 | raw (uncalibrated), noise 1 sd_types | +10.32 | +0.64 ± 0.052 | +0.32 |
| tabular_on/iid/stationary | 20 | raw (uncalibrated), noise 2 sd_types | +6.34 | -3.34 ± 0.060 | -1.67 |
| tabular_on/iid/stationary | 20 | mu_hat dispersion x0 | +8.21 | -1.47 ± 0.041 | -0.73 |
| tabular_on/iid/stationary | 20 | mu_hat dispersion x0.5 | +11.66 | +1.99 ± 0.044 | +0.99 |
| tabular_on/iid/stationary | 20 | mu_hat dispersion x1.5 | +11.81 | +2.14 ± 0.053 | +1.07 |
| tabular_on/iid/stationary | 20 | mu_hat dispersion x2 | +11.25 | +1.57 ± 0.054 | +0.79 |
| tabular_on/iid/stationary | 20 | tau_hat x0.5 | +10.18 | +0.50 ± 0.056 | +0.25 |
| tabular_on/iid/stationary | 20 | tau_hat x2 | +12.17 | +2.49 ± 0.052 | +1.25 |
| tabular_on/record/stationary | 20 | calibrated, noise 0 sd_types | +12.34 | +3.10 ± 0.052 | +1.55 |
| tabular_on/record/stationary | 20 | calibrated, noise 0.25 sd_types | +12.38 | +3.13 ± 0.048 | +1.57 |
| tabular_on/record/stationary | 20 | calibrated, noise 0.5 sd_types | +11.76 | +2.52 ± 0.047 | +1.26 |
| tabular_on/record/stationary | 20 | calibrated, noise 1 sd_types | +10.85 | +1.61 ± 0.042 | +0.80 |
| tabular_on/record/stationary | 20 | calibrated, noise 2 sd_types | +9.83 | +0.59 ± 0.030 | +0.29 |
| tabular_on/record/stationary | 20 | calibrated, noise 4 sd_types | +9.38 | +0.14 ± 0.016 | +0.07 |
| tabular_on/record/stationary | 20 | raw (uncalibrated), noise 0.5 sd_types | +12.04 | +2.80 ± 0.050 | +1.40 |
| tabular_on/record/stationary | 20 | raw (uncalibrated), noise 1 sd_types | +10.37 | +1.13 ± 0.052 | +0.57 |
| tabular_on/record/stationary | 20 | raw (uncalibrated), noise 2 sd_types | +6.68 | -2.56 ± 0.060 | -1.28 |
| tabular_on/record/stationary | 20 | mu_hat dispersion x0 | +7.92 | -1.32 ± 0.042 | -0.66 |
| tabular_on/record/stationary | 20 | mu_hat dispersion x0.5 | +11.22 | +1.98 ± 0.044 | +0.99 |
| tabular_on/record/stationary | 20 | mu_hat dispersion x1.5 | +11.92 | +2.67 ± 0.056 | +1.34 |
| tabular_on/record/stationary | 20 | mu_hat dispersion x2 | +11.29 | +2.04 ± 0.058 | +1.02 |
| tabular_on/record/stationary | 20 | tau_hat x0.5 | +10.03 | +0.79 ± 0.054 | +0.40 |
| tabular_on/record/stationary | 20 | tau_hat x2 | +12.19 | +2.95 ± 0.049 | +1.48 |
| tabular_on/iid/stationary | 40 | calibrated, noise 0 sd_types | +24.85 | +5.10 ± 0.071 | +2.55 |
| tabular_on/iid/stationary | 40 | calibrated, noise 0.25 sd_types | +25.31 | +5.57 ± 0.067 | +2.79 |
| tabular_on/iid/stationary | 40 | calibrated, noise 0.5 sd_types | +24.15 | +4.41 ± 0.057 | +2.20 |
| tabular_on/iid/stationary | 40 | calibrated, noise 1 sd_types | +22.74 | +3.00 ± 0.053 | +1.50 |
| tabular_on/iid/stationary | 40 | calibrated, noise 2 sd_types | +20.81 | +1.07 ± 0.044 | +0.54 |
| tabular_on/iid/stationary | 40 | calibrated, noise 4 sd_types | +19.90 | +0.16 ± 0.021 | +0.08 |
| tabular_on/iid/stationary | 40 | raw (uncalibrated), noise 0.5 sd_types | +24.33 | +4.59 ± 0.068 | +2.29 |
| tabular_on/iid/stationary | 40 | raw (uncalibrated), noise 1 sd_types | +20.75 | +1.01 ± 0.072 | +0.51 |
| tabular_on/iid/stationary | 40 | raw (uncalibrated), noise 2 sd_types | +12.90 | -6.84 ± 0.084 | -3.42 |
| tabular_on/iid/stationary | 40 | mu_hat dispersion x0 | +16.72 | -3.02 ± 0.058 | -1.51 |
| tabular_on/iid/stationary | 40 | mu_hat dispersion x0.5 | +23.46 | +3.72 ± 0.062 | +1.86 |
| tabular_on/iid/stationary | 40 | mu_hat dispersion x1.5 | +23.74 | +4.00 ± 0.075 | +2.00 |
| tabular_on/iid/stationary | 40 | mu_hat dispersion x2 | +22.60 | +2.86 ± 0.076 | +1.43 |
| tabular_on/iid/stationary | 40 | tau_hat x0.5 | +20.45 | +0.71 ± 0.080 | +0.35 |
| tabular_on/iid/stationary | 40 | tau_hat x2 | +24.30 | +4.56 ± 0.074 | +2.28 |
