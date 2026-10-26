# Example Sessions

These abridged sessions demonstrate decisions and state changes. Adapt structure, depth, and wording to the learner; do not copy them as fixed scripts.

## Single concept: why ice floats

**Learner request:** “Use Study to teach me why ice floats. I know basic chemistry.”

**Anchor question:** How does freezing water change its structure enough to make solid water float on liquid water?

**Initial context and core map:**

```text
phase change --reorganizes--> water molecules
water molecules --form--> hydrogen bonds
hydrogen bonds --favor during freezing--> open crystal lattice
open crystal lattice --increases--> volume per molecule
mass / volume --defines--> density
larger volume at similar mass --lowers--> ice density
liquid water --exerts--> buoyant force
lower density than liquid water --enables--> floating
```

Frontiers: Why is the solid lattice more open? Does trapped air matter? What follows for a freezing lake?

**You are here:** phase change → open lattice → density. Focus edge: `open lattice --lowers through greater volume--> density`.

**Diagnostic and learner evidence:** Ask, “If a bubble-free piece of ice were made under water, would it still float? Why?” Learner answers, “No; ordinary ice floats because freezing traps air.” Evidence suggests recognition of the outcome but a faulty causal edge from trapped air to low density.

**Graph and route mutation:** Add misconception `trapped-air-causes-ordinary-ice-buoyancy`; lower mastery of `open lattice --lowers--> density`; change route from mechanism-first to misconception repair. Expand only the molecular-spacing neighborhood. Contrast bubble-free ice with most solids, whose particles pack more closely after freezing.

**Representation rationale:** Use a two-frame particle-spacing sketch because hidden spatial arrangement, not vocabulary, is the bottleneck. Show equal numbers of molecules in differently sized outlines; label the sketch as schematic rather than a literal crystal projection.

```text
LIQUID: irregular, transient neighbors   ICE: stable open lattice
[ • •  • ]                              [ •    •    • ]
[  • • • ]                              [   •    •    • ]
same molecule count, compact volume      same molecule count, larger volume
```

**Active task:** “Assume both samples have the same mass. Which box has lower density, and which relationship in the map justifies your answer?” After the learner identifies greater volume and states \(\rho=m/V\), ask what happens to lake ice when denser liquid remains below it.

**Specific feedback and mastery update:** “You now connect open lattice to greater volume and greater volume to lower density. Your explanation of hydrogen bonds selecting that lattice still needs a cue.” Set node mastery `density=4`, `hydrogen-bond=2`, `open-lattice=3`; set edge mastery `volume-defines-density=4`, `open-lattice-increases-volume=3`, `hydrogen-bonds-favor-open-lattice=2`, `lower-density-enables-floating=4`.

**Recompressed map:**

```text
hydrogen bonding --stabilizes on freezing--> open ice lattice
open lattice --raises volume per mass--> lower density than liquid water
lower density --causes through buoyancy--> ice floating
```

**Synthesis:** Ice floats because freezing stabilizes an unusually open hydrogen-bonded lattice. Nearly unchanged mass occupies more volume, lowering density below that of liquid water; buoyancy then keeps ice at the surface.

**Transfer:** Predict how lake ecology would differ if solid water were denser than liquid water. Require a causal path, not merely “the lake freezes.”

**Review queue:** Next day—reconstruct the three-edge mechanism; three days—explain why trapped air is unnecessary; one week—predict the vertical freezing pattern of a lake from density relationships.

## Source-linked textbook chapter: population growth

**Evaluation note:** The source is the explicitly synthetic [population-growth fixture](../evals/fixtures/synthetic-chapter.md). Its page, section, figure, equation, examples, and data are fictional and exist only to test traceability.

**Learner request:** “Map this chapter before we study it. I want the argument, not paragraph memorization.”

**Anchor question:** Why does population growth often slow as population size rises, and what can the logistic model legitimately explain?

**Initial source-linked map:**

```text
unlimited resources --is an assumption of--> exponential baseline
  [p. 101, §7.1, ¶2]
rising density --can intensify--> competition, waste, or disease
  [p. 102, §7.2, ¶1]
density-dependent mechanisms --reduce--> net per-capita growth
  [p. 102, §7.2, ¶1]
(1 - N/K) --scales--> net per-capita growth
  [p. 102, §7.2, ¶2]
logistic equation --predicts--> zero net growth at N = K
  [p. 102, §7.2, Eq. 7.1]
curve fit --does not by itself identify--> biological mechanism
  [p. 103, §7.3, ¶2]
delayed feedback --can produce--> overshoot or oscillation
  [p. 104, §7.4, ¶2]
```

Chapter dependency: baseline → density feedback → formal model → two graphical views → pattern-versus-mechanism evidence → model limits. This reorders no claims but makes their dependencies explicit; the chapter itself states that argument at [p. 105, §7.5, ¶1](../evals/fixtures/synthetic-chapter.md#loc-p105-s7-5-p1).

Context links: the preceding chapter’s per-capita rates are prerequisites for interpreting \(r\); the following chapter expands candidate mechanisms behind density dependence. Both links come from [p. 105, §7.5, ¶2](../evals/fixtures/synthetic-chapter.md#loc-p105-s7-5-p2).

**You are here:** density feedback → logistic factor → net growth. Focus edge: `N=K --implies--> zero net growth`.

**Provenance check:** Exclude [Learner notes, LN-1](../evals/fixtures/synthetic-chapter.md#loc-learner-note-ln1) from the chapter-author map. It is explicitly learner-added, unrelated to the chapter, and factually false. If the learner asks about it, handle it as a separate misconception rather than laundering it into source content.

**Diagnostic and learner evidence:** Ask, “At \(N=K\), what exactly has become zero?” Learner answers, “Births stop because the habitat is full.” This reveals correct recognition of equilibrium but a faulty edge from carrying capacity to cessation of births.

**Graph and route mutation:** Add misconception `K-means-births-stop`; lower edge mastery for `N=K --implies--> zero net growth`; switch from top-down overview to equation-interpretation and contrast. Expand a tutor-added distinction: `birth rate - death rate --determines--> net growth`. Mark it as tutor explanation derived from, but not quoted from, [p. 102, §7.2, ¶1](../evals/fixtures/synthetic-chapter.md#loc-p102-s7-2-p1) and [p. 102, §7.2, ¶2](../evals/fixtures/synthetic-chapter.md#loc-p102-s7-2-p2). Preserve the author’s explicit statement in the latter locator that births and deaths may continue while balancing.

**Representation rationale:** Use the chapter’s paired graph idea because the bottleneck is confusing population-over-time with growth-rate-versus-population. The source describes both views at [p. 103, Fig. 7.1](../evals/fixtures/synthetic-chapter.md#loc-p103-fig7-1). If plotting is unavailable, use a labeled value table.

**Active task:** With \(r=0.4\), \(K=1{,}000\), compare the logistic factor and total growth at \(N=500\) and \(N=1{,}000\). Then explain why zero total growth need not mean zero births. Check against the synthetic worked values at [p. 103, §7.3, ¶1](../evals/fixtures/synthetic-chapter.md#loc-p103-s7-3-p1).

**Specific feedback and mastery update:** “Your calculation correctly gives a factor of one half at \(N=500\) and zero at \(N=K\). Your revised explanation now distinguishes demographic turnover from net change.” Set node mastery `carrying-capacity=3`, `net-growth=4`, `density-dependence=3`; set edge mastery `factor-scales-net-growth=4`, `N-equals-K-implies-zero-net-growth=4`, `curve-fit-is-insufficient-for-mechanism=2` because the last boundary has not yet been applied.

**Recompressed map:**

```text
rising population --changes through density dependence--> net per-capita growth
changed per-capita growth --is represented by--> logistic factor (1 - N/K)
logistic model --describes under assumptions--> population-growth pattern
pattern fit --is insufficient evidence for--> a particular mechanism
changing conditions or delay --limit--> fixed-r, fixed-K model
```

**Synthesis:** The chapter uses exponential growth as a deliberately simplified baseline, adds density-dependent feedback through the logistic factor, then separates mathematical pattern, biological mechanism, and model limits. It treats \(K\) as condition-dependent, not a timeless species ceiling.

**Transfer:** “A drought halves resource supply after a population has stabilized. Which parameter or assumption changes, and what transient behavior might the basic model miss?” Require source-supported claims plus clearly marked tutor inference.

**Review queue:** Next day—rebuild the chapter dependency map with locators; three days—contrast zero net growth with zero births; one week—diagnose the claim “a logistic fit proves competition caused the slowdown.”

## Mathematical and technical concept: gradient descent

**Learner request:** “I have 30 minutes to understand gradient descent well enough to explain how learning rate affects convergence. I understand derivatives.”

**Anchor question:** How can local slope information improve a model, and why does the step scale determine whether improvement is stable?

**Initial context and core map:**

```text
model parameters --produce--> predictions
predictions --are evaluated by--> loss
loss --has local slope summarized by--> gradient
negative gradient --selects--> local descent direction
learning rate --scales--> parameter update
parameter update --changes--> model parameters
repeated updates --may approach--> a minimum
objective geometry --limits--> stable step sizes
```

**You are here:** loss → gradient → parameter update. Focus edge: `learning rate --scales--> parameter update`.

**Diagnostic and learner evidence:** Ask, “Keeping the gradient fixed, what changes if the learning rate is multiplied by ten?” Learner answers, “It reaches the minimum ten times faster.” Derivative node appears secure; edge from learning rate to convergence behavior is faulty.

**Graph and route mutation:** Keep derivative prerequisites collapsed. Add misconception `larger-learning-rate-always-faster`; change route from brief formalization to misconception repair; expand only the learning-rate neighborhood:

```text
gradient --sets--> direction
learning rate --sets--> step magnitude
small steps --can cause--> slow progress
steps suited to geometry --can enable--> stable convergence
excessive steps --can cause--> overshoot, oscillation, or divergence
curvature --constrains--> useful step magnitude
```

**Representation rationale:** Use a numerical trajectory and, when plotting exists, a contour path. Movement across iterations and overshoot are the bottlenecks; an equation alone hides them.

For \(f(w)=w^2\), \(\nabla f=2w\), and \(w_0=4\):

| Learning rate \(\alpha\) | First update \(w_1=4-\alpha(8)\) | Pattern to inspect |
|---:|---:|---|
| 0.10 | 3.2 | same side, gradual approach |
| 0.50 | 0 | reaches minimum in this special quadratic case |
| 1.10 | -4.8 | crosses minimum with larger magnitude |

**Active task:** Predict \(w_1\), \(w_2\), and the qualitative path for \(\alpha=0.75\). Then explain which edge distinguishes direction from step magnitude. Expected trace: \(4\rightarrow-2\rightarrow1\), an alternating approach for this objective.

**Specific feedback and mastery update:** “You correctly used the negative gradient for direction and the learning rate for magnitude. You also recognized that crossing the minimum is not automatically divergence; increasing magnitude is the warning here.” Before repair: node mastery `gradient=3`, `learning-rate=2`; edge mastery `negative-gradient-selects-direction=3`, `learning-rate-scales-update=1`, `curvature-constrains-step=0`. After task: node mastery `learning-rate=4`; edge mastery `learning-rate-scales-update=4`, `step-size-affects-stability=4`, `curvature-constrains-step=2`.

**Recompressed map:**

```text
loss geometry --produces--> gradient
negative gradient × learning rate --forms--> parameter update
repeated updates --change depending on step scale and geometry--> convergence behavior
```

**Synthesis:** Gradient descent uses local slope to choose a descent direction and the learning rate to choose step magnitude. Faster initial movement is not equivalent to faster convergence: a useful rate must fit the objective’s geometry.

**Transfer:** Given a long narrow loss valley with steep curvature across it and shallow curvature along it, predict why one global learning rate may zigzag or progress slowly. Connect every prediction to the recompressed map.

**Review queue:** Later today—reconstruct the update rule in words; two days—compare rates on a new quadratic; one week—diagnose a training-loss curve that oscillates with growing amplitude.

## Historical and humanistic topic: French Revolution

**Learner request:** “Build a causal and chronological map of the French Revolution, then test connections rather than isolated dates.”

**Epistemic note:** This abridged example uses broad historical categories without source citations. A real session must consult suitable sources for precise claims. Causal weight, actor intent, periodization, and the roles of Enlightenment ideas, class interests, political contingency, and popular action remain interpretive and disputed; do not present one map as settled fact.

**Anchor question:** Why did strains within the ancien régime become a revolutionary crisis, and how did decisions and popular action transform that crisis?

**Initial causal and chronological map:**

```text
war debt and fiscal weakness --constrained--> monarchy
privilege and institutional resistance --obstructed--> tax reform
harvest stress and food prices --intensified--> popular grievance
representative dispute --shaped--> Estates-General crisis
political claims about sovereignty --challenged--> existing authority
Estates-General conflict --preceded and enabled--> National Assembly
popular mobilization --altered--> bargaining power and state authority
decisions, fear, and war --contributed contingently to--> radicalization
revolutionary measures --dismantled parts of--> ancien-régime institutions
```

Edge labels distinguish background constraint, proximate trigger, chronological precedence, enabling condition, action, and interpreted cause. Enlightenment influence belongs on the map with disputed causal weight, not as an unqualified single cause.

**You are here:** structural conditions → 1789 political crisis → institutional transformation. Focus edge: `subsistence stress --intensified--> popular grievance`.

**Diagnostic and learner evidence:** Ask, “If bread prices were the cause, what additional connection explains why hardship produced a regime crisis in 1789 rather than only unrest?” Learner answers, “High bread prices directly caused the Revolution.” Evidence shows knowledge of one trigger but a monocausal bridge from hardship to regime collapse.

**Graph and route mutation:** Add misconception `food-prices-alone-explain-revolution`; lower mastery of `food stress --intensified--> popular grievance` because learner treats intensification as sufficiency. Switch from chronological overview to causal-contrast route. Expand the neighborhood connecting fiscal incapacity, blocked reform, representation conflict, legitimacy, and mobilization. Retain uncertainty markers on relative causal weight.

**Representation rationale:** Pair a short timeline with a causal map because the bottleneck is conflating “came before” with “caused.” Static dual views suffice; animation adds no needed information.

```text
STRUCTURAL CONDITIONS       TRIGGERS/DECISIONS          TRANSFORMATIONS
fiscal weakness ---------> Estates-General crisis ---> sovereignty dispute
blocked reform ----------> representation conflict --> institutional change
subsistence stress ------> mobilization -------------> pressure on authority
```

**Active task:** Classify each arrow as necessary background, intensifier, trigger, enabling relation, direct action, consequence, or disputed interpretation. Then remove `popular mobilization` and predict which downstream edges weaken without claiming certainty about the counterfactual.

**Specific feedback and mastery update:** “You correctly treat food stress as an intensifier and connect fiscal weakness to the political confrontation. Your timeline still treats radicalization as inevitable, so contingency remains a frontier.” Set node mastery `fiscal-crisis=3`, `subsistence-stress=3`, `popular-mobilization=3`, `radicalization=2`; edge mastery `food-stress-intensifies-grievance=4`, `fiscal-weakness-constrains-monarchy=3`, `Estates-General-enables-sovereignty-conflict=3`, `war-contributes-to-radicalization=2`.

**Recompressed map:**

```text
fiscal and institutional constraints --made reform failure politically dangerous within--> ancien régime
representation conflict + claims of sovereignty --converted--> fiscal crisis into legitimacy crisis
popular action and elite decisions --redirected--> institutional change
war, fear, conflict, and contingency --shaped with disputed weights--> radicalization
```

**Synthesis:** Material hardship mattered, but it operated through fiscal, institutional, representational, and legitimacy relationships. Sequence constrained possibilities without making each later event inevitable. Different historians may defend different weights and turning points from different evidence.

**Transfer:** Compare this structure with another fiscal-political crisis. Identify one genuine structural analogy and one place the analogy fails. Alternatively, test the counterfactual: if tax reform had succeeded before 1789, which paths weaken and which grievances remain?

**Review queue:** Next day—rebuild causal and chronological maps separately; three days—explain why chronology is not sufficient causality; one week—defend and challenge one interpretation of radicalization using explicit evidence requirements.
