# Paper C theory working note, 17 November 2026

**ENGINEERING_ONLY.** Working derivations for T-C1–T-C3 in [the Paper C plan, §3.5](proposals/PAPER_C_SEQUENTIAL_POLICY_PLAN_20261104.md#35-relation-to-dac-and-to-paper-bs-theory). The 15 November PLAN decisions adopted the [STOP 4 reframing and census-first sequence](proposals/PAPER_C_REFRAME_AFTER_TRACKS_STOP4_20261115.md). The confirmatory node and channel list in R1-PAPERC-CORE remains open. Source checkout is `d224ad7e`.

The Paper B propositions used here are 8′, 10(a′) and 10(c) in `9ae6d877`, `docs/r1/proposals/T4_PROP10_REVISION_20261028.md`, read with the author-approved errata in PLAN §10 R1-T4-PROOF-CHECK at `04ce814c`. Proposition 8′ gives the Bayes immediate decision at a fixed observed history. Proposition 10(a′) gives campaign optimality for a fixed price under no feedback (NF) and no information (NI). Hard budgets, recurring latent sensitivity, and selected incumbent measurement errors motivate distinct departures from that setting. Departures identify where to look for a gain. Their magnitude and decision relevance are empirical questions.

## T-C1 — Hard budget and a static price

**Setting and bound.** After any common forced first trial, there are $n\ge1$ slots and $0\le k\le n$ available runs. Every eligible execution costs one run and yields a nonnegative expected gain $X_t\le M$ under the Bayes keep rule. The observable offers $X_t$ and eligibility flags are i.i.d. Action choices leave future opportunities unchanged, including their information available to the controller. Represent a rule skip by $X_t=0$. A static rule uses one cutoff, optionally randomizes independently across slots at that cutoff, and stops accepting when the cap is full.

Set $q=k/n$. For $0<q\le\Pr(X>0)$ choose $\lambda\ge0$ and a tie probability so that $\Pr(\text{static rule would accept})=q$, ignoring the cap. Let $S$ count these planned accepts and let $\mu_\lambda=\mathbb E[X\mid\text{planned accept}]$. The dynamic policy's gain over the best static rule allowing ties obeys
$$
0\le V^\star-V_{\mathrm{stat}}^\star
\le \mu_\lambda\,\mathbb E(S-k)^+
\le \tfrac12\mu_\lambda\sqrt{k(1-k/n)},\qquad S\sim\mathrm{Bin}(n,q).
$$

**Proof.** On each offer sequence the sum of accepted offer values is at most $\lambda k+\sum_t(X_t-\lambda)^+$. The uncapped quantile rule attains the expectation of this relaxation because its expected count is $k$ and it accepts every offer strictly above $\lambda$. Conditional on the acceptance indicators, the offered rewards of accepted slots have common mean $\mu_\lambda$. Thus truncating the quantile rule to its first $k$ accepts loses exactly $\mu_\lambda\mathbb E(S-k)^+$. The last inequality follows from $\mathbb E(S-k)=0$ and Cauchy–Schwarz. If $q>\Pr(X>0)$, accepting all positive offers up to $k$ yields the same bound with $\lambda=0$, $S\sim\mathrm{Bin}(n,\Pr(X>0))$, and the exact overflow term. The variance shortcut above is for the matched-mean case. A constant positive offer on every eligible slot gives exact equality of dynamic and static values, even when the budget binds. For $k=0$, all feasible values are zero.

**Sharpness and comparison class.** With $n=2,\ k=1$ and equally likely offers $1,3$, the optimal policy saves its run after a first offer of 1 and takes either offer in the last slot. Its value is 2.5. The best static rule takes only 3 and has value 2.25. Accepting 1 with probability $r$ while always accepting 3 gives $(9-r^2)/4$, so randomizing at that cutoff leaves the gap intact. For an i.i.d. finite-support law, Arlotto and Gurvich prove bounded regret of an adaptive rule against the offline optimum. Their Theorem 3 also lower-bounds the regret of nonadaptive rules by order $\sqrt n$ in its interior budget range. Together the results permit a dynamic-versus-static gap of order $\sqrt n$ there. A deterministic cutoff on an atomic law can miss the required quantile. In that case the exact comparison uses the deterministic cutoff class. [Arlotto and Gurvich (2019), Theorems 1 and 3 and Lemma 3](https://arxiv.org/abs/1710.07719).

**E-SYN check.** The exact recursion in [`paperc.esyn.dp`](../src/paperc/esyn/dp.py) applies to `strict_null` and `budget`. On their three positive offer levels, enumerate the thresholds at each level, zero and a threshold above the largest offer. This evaluates every deterministic cutoff class. Including the common first-trial mean, `budget` gives $0.011391628$ for the DP and $0.009276652$ for the best deterministic static rule, a gap of $0.002114976$. The matched-mean randomized quantile rule has value $0.010350368$, and its dual upper bound is $0.012051785$. In `strict_null` both the DP and the static rule give $0.017589431$. These are model expectations. The [accepted oracle report](reports/ESYN_ORACLE_TABLE_20261116.md) also gives a paired simulation check.

## T-C2 — Value of one latent-sensitivity measurement

**Single future keep decision.** At a fixed history let the future true gain $X$ and the prospective signal $H$ be jointly Gaussian. With $m=\mathbb E X$ and $s=|\operatorname{Cov}(X,H)|/\sqrt{\operatorname{Var} H}$, the posterior mean given $H$ is distributed as $m+sZ$ for $Z\sim N(0,1)$. Use $s=0$ for a degenerate signal. Write $\nu(m,s)=\mathbb E(m+sZ)^+$. Keeping yields the unknown $X$, and discarding yields zero, so for $s>0$ the expected value of seeing $H$ is
$$
\nu(m,s)-m^+
=s\phi(|m|/s)-|m|\Phi(-|m|/s)
\ \le\ s/\sqrt{2\pi}.
$$
It is zero at $s=0$ and reaches the bound at $m=0$. This is the expected gain from optimizing a binary terminal decision after a Gaussian posterior update. In the independent-noise latent model $H=\alpha\theta+\epsilon$, $X=\beta\theta+\eta$, $\operatorname{Var}\theta=\tau^2$, and $\operatorname{Var}\epsilon=\sigma_H^2$, we have $s=|\alpha\beta|\tau^2/\sqrt{\alpha^2\tau^2+\sigma_H^2}$. All quantities are conditional on the current history. [Frazier, Powell and Dayanik (2009), §3](https://people.orie.cornell.edu/pfrazier/pub/CorrelatedKG.pdf).

**One future execute–keep pair.** Give the future edit its own comparison $Y$ after execution at fixed price $g$. Assume joint Gaussianity of $X,H,Y$, unchanged future feasibility, and no feedback. The conditional standard deviations of the posterior-mean increments from $Y$ given $H$, and from $Y$ alone, are $u$ and $u_0$, respectively. Let $B=\nu(m+sZ,u)$, and $B_0=\nu(m,u_0)$. The exact continuation value of revealing $H$ is
$$
K=\mathbb E(B-g)^+-(B_0-g)^+,\qquad
0\le K\le \tfrac12s+\frac{\sqrt{s^2+u^2}-u_0}{\sqrt{2\pi}}.
$$
Ignoring $H$ is feasible, giving the lower bound. Joint Gaussianity and iterated conditional expectation give $\mathbb E B=\nu(m,\sqrt{s^2+u^2})$ and $\sqrt{s^2+u^2}\ge u_0$. The positive part is 1-Lipschitz, so the increase from replacing $B_0$ by $\mathbb E B$ is at most $\mathbb E B-B_0$. Since $\partial_v \nu(m,v)=\phi(m/v)$ for $v>0$, this is bounded by the second term. The remaining Jensen gap is at most $\tfrac12\mathbb E|B-\mathbb E B|$, using $x^+=(x+|x|)/2$. The map $z\mapsto\nu(m+sz,u)$ is $s$-Lipschitz. The independent-copy formula for variance gives $\operatorname{Var}(B)\le s^2$, yielding the first term.

If a probe would be skipped by the immediate rule and has immediate expected keep gain $r_{\mathrm p}<g$, the optimal advantage over that rule in the probe-plus-one-future-edit setting is $[K-(g-r_{\mathrm p})]^+$. Thus a probe can be ruled out in this setting when the upper bound on $K$ is at most $g-r_{\mathrm p}$. For Prop. 10(c) the noiseless probe reveals $\theta$, so $s=\beta,\ u=0,\ u_0=\beta/\sqrt{1+\kappa^2}$ with $m=0$. The advantage grows linearly with $\beta$ for $\kappa>0$ and fixed $\alpha,g$ with $g>\alpha\phi(0)$. At $(\alpha,\beta,g,\kappa)=(1,0.1,0.5,1)$ the forced-probe contrast is $-0.1010577$ and the optimal advantage is zero, as specified by the author erratum.

**E-SYN scope.** The `information` world schedules follow-ups when the probe is proposed and shares sensitivities across probe and follow-up increments. It also has several future offers and $W=10$. Its certified family comparison measures a campaign gain in that joint setting. The one-future-edit formula applies to a matched visible-versus-masked comparison with a fixed follow-up and common feasible actions. The accepted budget DP has fresh keys and independent comparisons. It supplies a no-information control. The shared-incumbent-error world instead changes future comparison states and feasibility after keeps and re-audits.

## T-C3 — One supervised policy-improvement step

**Setting and bound.** In a finite-horizon Markov model with time, remaining resources and belief in the state, let $\pi$ be one fixed continuation policy. Include an absorbing state so all trajectories share a horizon, and let $d_t^\rho$ be the state law at step $t$ under policy $\rho$. The exact binary fork contrast is $D_t(s)=Q_t^\pi(s,1)-Q_t^\pi(s,0)$. A supervised rule $\hat\pi$ chooses an action according to the sign of $\widehat D_t$ and follows it every time the decision recurs. Put $e_t(s)=\max_a Q_t^\pi(s,a)-Q_t^\pi(s,\hat\pi_t(s))$ and $\Delta_{t+1}=V_{t+1}^\star-V_{t+1}^\pi$. For feasible actions,
$$
e_t(s)\le|\widehat D_t(s)-D_t(s)|,\qquad
J^\star-J(\hat\pi)
\le \sum_t\mathbb E_{s\sim d_t^{\hat\pi}}\!
   \left[e_t(s)+\operatorname{span}_{a}\mathbb E[\Delta_{t+1}(S')\mid s,a]\right].
$$
The first inequality charges the true margin only when the learned sign chooses a suboptimal action for $Q^\pi$. For the second, $Q_t^\star(s,a)=Q_t^\pi(s,a)+\mathbb E[\Delta_{t+1}(S')\mid s,a]$. Subtract $Q_t^\star(s,\hat\pi_t(s))$ from the maximum and telescope the resulting per-step losses along $\hat\pi$. The same telescoping argument around $V^\pi$ gives $J(\hat\pi)-J(\pi)\ge-\sum_t\mathbb E_{d_t^{\hat\pi}}e_t$. A state with one feasible action contributes zero. Exact greedy rollout improves the base policy. A small remaining gap requires both accurate fork signs on deployed histories and a small action-dependent future residual. If $d_t^{\hat\pi}/\mu_t\le C_t$ for the fork-state law $\mu_t$, the sign-loss expectation is at most $\sqrt{C_t\,\mathbb E_{\mu_t}(\widehat D_t-D_t)^2}$. This uses error against the conditional contrast, which needs audit replicates or a model reference when labels are noisy. [Kakade and Langford (2002), §§6–7](https://people.eecs.berkeley.edu/~pabbeel/cs287-fa09/readings/KakadeLangford-icml2002.pdf).

**Counterexample.** At step 1 a safe action gives 1 and stops, while entering a second state gives zero immediate reward. At step 2 the base policy would choose zero there, although a payoff $L>1$ is feasible. One exact greedy update chooses the safe action at step 1 and changes the unreachable step-2 decision. Optimal value is $L$ and updated value is 1. Even complete exact fork labels allow an arbitrarily large gap here.

**Exact E-SYN check.** Let $B_j(w)$ be the value of the best deterministic static rule in the T-C1 benchmark with $j$ slots and $w$ runs left after the forced first trial. The rollout executes iff $X\ge B_{j-1}(w)-B_{j-1}(w-1)$ at an eligible proposal. Evaluate this new threshold table by backward induction with its own future values, charging the same forced first trial. For `budget` this gives $0.010531719$, between static $0.009276652$ and optimal $0.011391628$. One exact update captures 59.34% of that gap and leaves $0.000859909$. In `strict_null` all three agree. The remaining gap isolates the rollout target itself, since the recursion uses exact contrasts throughout the feasible budget states.

**P6 and Q3 scope.** The [accepted P6 fork implementation](../src/paperc/forks.py) scores single deviations from logged decisions on root histories. Its default average over distinct continuation policies estimates their average contrast. The bound above uses one continuation consistently and expectations under the deployed rule. The P6 scores and sparse-root interval checks establish estimator behaviour in E-SYN. Full-campaign equivalence for Q3 remains a separate test against the frozen, matched comparator and the author-declared gap.

## Verification status

The proofs above are restricted working results. Deterministic checks reproduced the two existing DP values, the best-static enumeration, exact binomial overflow, the noiseless-probe formula and the stated rollout gap at `d224ad7e`. They used the checked-in E-SYN laws and no generated campaign data. The real-node transfer, final theory scope, and confirmatory protocol remain open.
