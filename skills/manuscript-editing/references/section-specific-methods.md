# Methods-Specific Editing Guidelines

**Purpose:** Provide complete, reproducible protocols enabling independent replication.

**Key principle:** Methods must contain enough detail for another lab to repeat experiments exactly.

---

## Critical Requirements for Complete Reproducibility

### 1. Reagent Specificity

**For ALL reagents, antibodies, chemicals, and biologicals:**

**Required information:**
- ☐ Vendor/manufacturer name
- ☐ Catalog number
- ☐ Lot number (if critical for reproducibility, e.g., antibodies)
- ☐ Concentration/dilution used
- ☐ Units specified

**Example (complete):**
> "Anti-H3K9me3 antibody (Abcam, ab8898, lot# GR3256789-1; 1:2,000 dilution in 5% BSA/TBST) was incubated overnight at 4°C."

**Example (incomplete—DO NOT accept):**
- ❌ "H3K9me3 antibody was used" (no vendor, no dilution)
- ❌ "Abcam antibody (1:1,000)" (no catalog#)
- ❌ "Anti-H3K9me3 (ab8898)" (no vendor, no dilution)

**Common reagent types requiring details:**

**Antibodies (primary and secondary):**
- Vendor, catalog, lot (optional but recommended), dilution, diluent

**Chemicals/compounds:**
- Vendor, catalog, concentration, solvent, storage conditions

**Cell lines:**
- Source (ATCC, lab name), passage number, authentication method

**Mouse strains:**
- Source (Jackson Labs, in-house), strain numbers, genotyping primers

**Plasmids/constructs:**
- Source (Addgene, lab), plasmid ID, modifications made

**Kits:**
- Vendor, catalog, kit name, any protocol deviations

---

### 2. Equipment Specifications

**For major equipment, include:**
- ☐ Manufacturer
- ☐ Model number
- ☐ Key settings used

**Examples:**
- Microscope: "Confocal images were acquired using a Zeiss LSM 880 with 63× oil-immersion objective (NA 1.4)"
- Flow cytometer: "Flow cytometry was performed on a BD FACSAria II"
- Sequencer: "RNA sequencing was performed on an Illumina NovaSeq 6000"
- Centrifuge: "Cells were pelleted at 300g for 5 min at 4°C (Eppendorf 5424R)"

---

### 3. Experimental Procedures (Step-by-Step)

**For each experimental procedure, include:**

**Timing:**
- Incubation times: "overnight at 4°C" or "2 h at room temperature"
- Reaction times: "30 min at 37°C"
- Duration of treatments: "cells were treated for 48 h"

**Temperatures:**
- Incubation temperature: "37°C, 5% CO₂"
- Storage temperature: "−80°C"
- Reaction temperature: "room temperature (20-22°C)"

**Volumes:**
- Reagent volumes: "100 μL per well"
- Culture volumes: "cells in 10 mL medium"
- Dilution volumes: "1:1,000 in 5 mL TBST"

**Steps in order:**
- Logical sequence
- All critical steps included
- Wash steps specified
- Blocking steps detailed

**Example (complete protocol):**
> "Cells were fixed in 4% paraformaldehyde for 15 min at room temperature, washed three times with PBS, and permeabilized with 0.1% Triton X-100 for 10 min. After blocking in 5% normal goat serum for 1 h, cells were incubated with anti-H3K9me3 (Abcam, ab8898; 1:2,000) overnight at 4°C, washed three times with PBST, and incubated with Alexa Fluor 488-conjugated anti-rabbit secondary antibody (Invitrogen, A11008; 1:1,000) for 1 h at room temperature. Nuclei were counterstained with DAPI (1 μg mL⁻¹)."

---

### 4. Statistical Analysis Section (MANDATORY)

**Must include comprehensive statistical methods:**

**Sample size determination:**
- How n was chosen
- Power analysis (if performed)
- Justification for sample size

**Example:**
> "Sample sizes were determined based on pilot experiments showing 30% variance. To detect a 40% difference with 80% power at α = 0.05, we calculated n = 8 mice per group."

**Data distribution:**
- Normality testing: "Normality was assessed using Shapiro-Wilk test"
- Outlier detection: "Outliers were identified using Grubbs' test and excluded (n = 2 samples)"

**Statistical tests used:**
- Which test for which comparison
- Rationale for test choice
- Multiple testing corrections

**Example:**
> "For comparisons between two groups, two-tailed Student's t-test was used after confirming normal distribution. For multiple groups, one-way ANOVA with Tukey's post hoc test was performed. For non-normally distributed data, Mann–Whitney U test was used. Survival curves were compared using log-rank test."

**Significance threshold:**
> "Statistical significance was set at P < 0.05 for all tests."

**Software used:**
- "Statistical analyses were performed using GraphPad Prism 9.0 (GraphPad Software)"
- "R version 4.1.0 (R Foundation for Statistical Computing)"
- "Python 3.9 with SciPy and NumPy libraries"

**Replication:**
- "All experiments were performed with at least three biological replicates unless otherwise noted."
- "Representative images shown are from one of three independent experiments."

**Error bars:**
- "Data are presented as mean ± s.d. unless otherwise indicated."
- "Box plots show median (center line), 25th-75th percentiles (box), and min-max (whiskers)."

---

### 5. Regulatory Approvals

**Animal studies:**
- ☐ IACUC approval number
- ☐ Institution name
- ☐ Guideline compliance (e.g., ARRIVE guidelines)

**Example:**
> "All animal procedures were approved by the Institutional Animal Care and Use Committee of Stanford University (protocol #12345) and performed in accordance with ARRIVE guidelines."

**Human studies:**
- ☐ IRB approval number
- ☐ Informed consent statement
- ☐ Ethical compliance statement

**Example:**
> "Human studies were approved by the Institutional Review Board of Massachusetts General Hospital (protocol #2021P000123). All participants provided written informed consent."

**Biosafety:**
- If working with infectious agents, toxins, or recombinant DNA:
> "All work with recombinant lentivirus was performed in BSL-2 facilities approved by the Institutional Biosafety Committee (protocol #Bio-456)."

---

### 6. Data Availability

**Must include:**

**Raw data repositories:**
- "RNA sequencing data are deposited in GEO under accession number GSE123456"
- "Mass spectrometry data are available at ProteomeXchange (PXD012345)"
- "Imaging data are available at BioImage Archive (S-BIAD123)"

**Code availability:**
- "Custom analysis scripts are available at GitHub (github.com/username/repo)"
- "Source code for analysis pipeline is provided as Supplementary Software"

**Materials availability:**
- "Mouse strains are available from Jackson Laboratory (strain #012345)"
- "Plasmids are available from Addgene (plasmid #67890)"
- "Reagents are available from corresponding author upon reasonable request"

**Restrictions (if any):**
- "Materials transfer agreement required for cell line distribution"
- "Data available upon publication and reasonable request"

---

## Methods Editing Checklist

**Reagent Completeness:**
- [ ] All antibodies: vendor, catalog, dilution
- [ ] All chemicals: vendor, catalog, concentration, units
- [ ] All cell lines: source, authentication
- [ ] All mouse strains: source, genotyping details
- [ ] All kits: vendor, catalog, deviations noted

**Experimental Detail:**
- [ ] All incubation times specified
- [ ] All temperatures specified
- [ ] All volumes include units
- [ ] Step-by-step order logical
- [ ] Washing/blocking steps detailed

**Equipment:**
- [ ] Major equipment: manufacturer, model
- [ ] Microscope: objective, NA, settings
- [ ] Sequencers/analyzers: model specified
- [ ] Software: version numbers

**Statistical Methods:**
- [ ] Sample size justification
- [ ] Normality testing described
- [ ] All tests named and justified
- [ ] Multiple testing corrections stated
- [ ] Significance threshold stated (P < 0.05)
- [ ] Software specified with version
- [ ] Replication described (biological vs. technical)
- [ ] Error bar definitions

**Regulatory:**
- [ ] IACUC/IRB approval numbers
- [ ] Guideline compliance (ARRIVE, etc.)
- [ ] Consent statements for human studies

**Data Availability:**
- [ ] Repository names and accession numbers
- [ ] Code availability stated
- [ ] Materials availability stated

---

## Common Methods Issues and Fixes

**Issue 1: Missing Reagent Details**

**❌ INCOMPLETE:**
> "We used Western blotting to measure proteins. Antibodies were from commercial sources."

**✅ COMPLETE:**
> "We used Western blotting to measure protein levels. Primary antibodies: anti-H3K9me3 (Abcam, ab8898; 1:2,000), anti-SUV39H1 (Cell Signaling Technology, #8729; 1:1,000), anti-β-actin (Sigma-Aldrich, A5316; 1:5,000). Secondary antibodies: HRP-conjugated anti-rabbit (Jackson ImmunoResearch, 111-035-003; 1:10,000) and anti-mouse (Jackson ImmunoResearch, 115-035-003; 1:10,000)."

---

**Issue 2: Missing Protocol Specifics**

**❌ INCOMPLETE:**
> "Standard Western blotting protocols were followed."

**✅ COMPLETE:**
> "Cells were lysed in RIPA buffer (50 mM Tris-HCl pH 7.4, 150 mM NaCl, 1% NP-40, 0.5% sodium deoxycholate, 0.1% SDS) with protease inhibitors (Roche, cOmplete Mini, 11836153001). Protein concentrations were determined by BCA assay (Thermo Fisher, 23225), and 30 μg total protein was separated on 4-12% Bis-Tris gels (Invitrogen, NP0335), transferred to PVDF membranes (Millipore, IPVH00010), blocked in 5% milk in TBST for 1 h at room temperature, and incubated with primary antibodies overnight at 4°C. After washing three times with TBST, membranes were incubated with HRP-conjugated secondary antibodies for 1 h at room temperature and developed using ECL substrate (GE Healthcare, RPN2232)."

---

**Issue 3: Incomplete Statistical Section**

**❌ INCOMPLETE:**
> "Statistics were done with Student's t-test. P < 0.05 was significant."

**✅ COMPLETE:**
> "Sample sizes were determined based on prior studies showing 25% effect size. Normality was assessed using Shapiro-Wilk test. For two-group comparisons with normal distribution, two-tailed Student's t-test was used. For multiple groups, one-way ANOVA with Tukey's post hoc test was performed. For non-normally distributed data, Mann–Whitney U test was applied. Survival curves were compared using log-rank test. Multiple testing correction was applied using Bonferroni method when appropriate. Statistical significance was set at P < 0.05. All analyses were performed using GraphPad Prism 9.0. Data are presented as mean ± s.d. unless otherwise stated. All experiments include at least three biological replicates."

---

**Issue 4: Missing Equipment Details**

**❌ INCOMPLETE:**
> "Images were taken using confocal microscopy."

**✅ COMPLETE:**
> "Confocal images were acquired using a Zeiss LSM 880 confocal microscope with 63× oil-immersion objective (NA 1.4). Z-stacks were acquired at 0.5-μm intervals. Images were processed using Fiji (ImageJ version 1.53c) with identical settings across all samples. Quantification was performed using CellProfiler 4.0."

---

**Issue 5: Missing Approvals**

**❌ INCOMPLETE:**
> "Animal experiments were approved."

**✅ COMPLETE:**
> "All animal procedures were approved by the Institutional Animal Care and Use Committee of Stanford University (protocol #31245) and conducted in accordance with ARRIVE guidelines and NIH Guide for the Care and Use of Laboratory Animals."

---

## Methods Quality Standards (CNS-Level)

**Gate 1: Complete Reagent Information**
- [ ] All antibodies: vendor + catalog + dilution
- [ ] All chemicals: vendor + catalog + concentration + units
- [ ] All cell lines: source + authentication
- [ ] All biological materials: source + identifiers

**Gate 2: Reproducible Protocols**
- [ ] Step-by-step procedures
- [ ] All times, temperatures, volumes specified
- [ ] Equipment with manufacturer + model
- [ ] Software with version numbers

**Gate 3: Comprehensive Statistics**
- [ ] Sample size justification
- [ ] All tests named and justified
- [ ] Normality testing described
- [ ] Significance threshold stated
- [ ] Software specified
- [ ] Replication defined

**Gate 4: Regulatory Compliance**
- [ ] IACUC/IRB approval numbers
- [ ] Guideline compliance stated
- [ ] Ethical statements included

**Gate 5: Data Accessibility**
- [ ] Repository accession numbers
- [ ] Code availability
- [ ] Materials availability

---

## Example Methods Subsection (Complete)

**Cell Culture and Treatment**

> "Human embryonic kidney 293T cells (ATCC, CRL-3216) were cultured in DMEM (Gibco, 11965092) supplemented with 10% fetal bovine serum (Sigma-Aldrich, F2442, lot# SLCD5264) and 1% penicillin-streptomycin (Gibco, 15140122) at 37°C with 5% CO₂. Cells were authenticated by short tandem repeat profiling and tested negative for mycoplasma (MycoAlert kit, Lonza, LT07-318). For iron depletion experiments, cells were treated with 100 μM deferoxamine (Sigma-Aldrich, D9533) or vehicle (PBS) for 24 h. For rescue experiments, ferric ammonium citrate (Sigma-Aldrich, F5879) was added at 50 μg mL⁻¹ for 48 h."

**Why this is complete:**
- ✅ Cell line source with catalog
- ✅ All media components with vendor + catalog + lot (for critical reagents)
- ✅ Culture conditions (temperature, CO₂)
- ✅ Authentication method
- ✅ Mycoplasma testing
- ✅ Treatment concentrations with units
- ✅ Treatment durations
- ✅ Vehicle controls specified

---

## Editorial Notes for Missing Information

**When methods lack detail, flag in editorial summary:**

> **[EDITORIAL NOTE: Methods—Please add the following details for reproducibility]:**
> - Antibodies: Add vendor, catalog numbers, and dilutions for all primary and secondary antibodies
> - Statistical analysis: Add sample size justification, normality testing, and multiple testing corrections
> - Equipment: Add manufacturer and model numbers for microscope, flow cytometer, and sequencer
> - Protocols: Add incubation times, temperatures, and volumes for immunostaining protocol
> - Approvals: Add IACUC protocol number and institution name

**NEVER fabricate missing details—always flag for author to add**

---

## References

**For statistical reporting:**
- See `references/section-specific-results.md` for test descriptions

**For metacognitive self-checks:**
- See `references/meta-editing-metacognitive-checklist.md`

---

**Remember:** Methods reproducibility is non-negotiable for CNS journals. Every detail matters for independent replication.
