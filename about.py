from shiny import App, render, ui, reactive
import pandas as pd

code_str_for_CI_OTE = '''
from scipy.stats import beta
import numpy as np

def ci_ote(n, o, e, cl=0.95):
    """
    Calculates the "confidence interval" for OTE

    Parameters
    ----------
    n : int
        number of observations
    o : float, non-negative
        number of observed events
    e : float, positive
        number of expected events:
    cl : float, optional
        the confidence level, by default 0.95

    Returns
    -------
    numpy.array
        the left and right end points of the "CI for OTE"
    """
    # CI for "true event probability"
    dist = beta(a=(1 / 2 + o), b=(1 / 2 + n - o))
    ci_event_prob = np.array([
        dist.ppf((1 - cl) / 2), dist.ppf((1 + cl) / 2)
    ])
    # correction at edges
    if o == 0:
        ci_event_prob[0] = 0
    if n == o:
        ci_event_prob[1] = 1
    # CI for "OTE"
    ci = ci_event_prob * n / e
    return ci
'''

example_results_df_html = """\
    <table border=1 frame=hsides rules=rows style="table-layout: fixed; width: 100%; margin: 10px auto;">
    <tr style="border-top: thin solid; border-bottom: thin solid;">
        <th>n</th>
        <th>o</th>
        <th>e</th>
        <th>OTE</th>
        <th>conf. lvl.</th>
        <th>"OTE CI"</th>
        <th>p-val</th>
        <th>adj. p</th>
    </tr>
    <tr>
        <td>41</td>
        <td>11</td>
        <td>5.6</td>
        <td>1.964</td>
        <td>0.95</td>
        <td>(1.11, 3.05)</td>
        <td>0.02 *</td>
        <td>0.04 *</td>
    </tr>
    <tr>
        <td>5</td>
        <td>1</td>
        <td>0.4</td>
        <td>2.5</td>
        <td>0.95</td>
        <td>(0.28, 7.86)</td>
        <td>0.29</td>
        <td>0.29</td>
    </tr>
    </table>
"""

what_is_it_for = ui.tags.section(
    ui.tags.h1("What is it for?"),
    ui.tags.p(
        "A useful metric for monitoring calibration of a predictive model for discrete events is the observed-to-expected events ratio (OTE). ",
    ),
    ui.tags.ul(
        ui.tags.li(
            "E.g. a conversion model predicts that 5.6 out of 41 customers will convert, when in reality 11 of them did."
        ),
        ui.tags.li(
            "Then we have an OTE = 11 / 5.6 = 1.96."
        ),
    ),
    ui.tags.p(
        "Or consider a similar numerical examples, in a less happy context:"
    ),
    ui.tags.ul(
        ui.tags.li(
            "An underwriting model predicts that 5.6 out of 1,324 borrowers will default on their loans, when in reality 11 of them did. ",
        ),
        ui.tags.li(
            "Then we have OTE = 11 / 5.6 = 1.96 times the expected loan losses. "
        ),
        ui.tags.li(
            "Notice that the much larger customer base (1,324 vs 41) does not enter the OTE calculation. "
        ),
    ),
    ui.tags.p(
        "As the examples above illustrate:"
    ),
    ui.tags.ul(
        ui.tags.li(
            "An significant OTE deviation from 1, in either direction, would indicate model miscalibration, and calls for action."
        ),
    ),
    ui.tags.p(
        "One might wonder... "
    ),
    ui.tags.ul(
        ui.tags.li(
            "... if reading from a small sample size (e.g. 41) is reliable at all, "
        ),
        ui.tags.li(
            "... and whether we can put an \"confidence interval\" around OTE. "
        ),
        ui.tags.li(
            "... or if the size of the customer base (e.g. 41 vs 1,324) affects the conclusions. "
        ),
    ),
    ui.tags.p(
        "This calculator quantifies the uncertainty in the observed-to-expected (OTE) metric, and answers these questions. "
    ),
    ui.tags.p("Example usages:"),
    ui.tags.h5('"What\'s my model calibration level?"'),
    ui.tags.ul(
        ui.tags.li(
            ui.tags.i("Uncertainty estimates: "),
            "A product manager sees an OTE of 1.96 in a new customer segment (11 observed events, 5.6 expected, out of 41 customers). "
            "How much confidence do we have in the OTE? "
            "What about another segment that has an OTE of 2.5 (1 observed event, 0.4 expected, out of 5 customers)?",
        ),
        ui.tags.li(
            ui.tags.i("Early reads: "),
            "A new product launched, with very few customers so far, and no observed events, hence an OTE of 0. "
            "How good is our prediction when OTE reads 0?",
        ),
    ),
    ui.tags.h5('"Which subgroup should I prioritize?"'),
    ui.tags.ul(
        ui.tags.li(
            ui.tags.i(
                "p-values, hypotheses ranking, and multiple testing adjustments: "
            ),
            "A data scientist is going over a list of suspicious subgroups of customers, each with an OTE greater than 1. "
            "But the subgroups also come at different sample sizes. "
            "How should we rank the list of subgroups, in terms of strengths of evidence of miscalibration? "
            "How should we account for multiple testing and p-fishing?",
        ),
    ),
    ui.tags.h4(ui.tags.i("An illustration")),
    ui.tags.p(
        "We illustrate how the calculator solves these problems, using the first example above,  "
    ),
    ui.tags.ul(
        ui.tags.li(
            "Subgroup 1: 41 customers (n=41), 11 observed events (o=11), 5.6 expected events (e=5.6)."
        ),
        ui.tags.li(
            "Subgroup 2: 5 customers (n=5), 1 observed events (o=1), 0.4 expected events (e=0.4)."
        ),
    ),
    ui.tags.p("Results are as in the table below: "),
    ui.HTML(example_results_df_html),
    ui.tags.ul(
        ui.tags.li(
            ui.tags.i("OTE"),
            ": the point estimate of calibration level. ",
            ui.tags.ul(
                ui.tags.li(
                    "In this case, both are larger than 1.",
                ),
                ui.tags.li(
                    "Note that Subgroup 2 has a higher OTE (5.0) than Subgroup 1 (1.964).",
                ),
            ),
        ),
        ui.tags.li(
            ui.tags.i("conf. lvl."),
            ": the confidence level at which the CI is calculated. ",
            ui.tags.ul(
                ui.tags.li(
                    "This is part of the user-specified input.",
                ),
            ),
        ),
        ui.tags.li(
            ui.tags.i('"OTE CI"'),
            ": the interval estimate of calibration level. ",
            ui.tags.ul(
                ui.tags.li(
                    "If the interval does not contain 1, we claim evidence of miscalibration, at the specified confidence level.",
                ),
                ui.tags.li(
                    "The wider the CI, the less certain we are of the calibration level.",
                ),
                ui.tags.li(
                    "In this case, the CI for Subgroup 1 (1.11, 3.05) does not contain 1. "
                ),
                ui.tags.li(
                    "In contrast, Subgroup 2, with only 5 samples, has a much wider CI (0.28, 7.86) which contains 1. ",
                ),
                ui.tags.li(
                    "Data shows significant evidence of miscalibration for Subgroup 1, but weaker evidence for Subgroup 2. "
                ),
            ),
        ),
        ui.tags.li(
            ui.tags.i("p-val"),
            ': the p-value for the formal test of hypothesis "the model is calibrated". ',
            ui.tags.ul(
                ui.tags.li(
                    "A smaller p-value indicates stronger evidence of model miscalibration.",
                ),
                ui.tags.li(
                    "p-values below common thresholds (0.05, 0.01, 0.001) are labeled with significance markers (*, **, ***).",
                ),
                ui.tags.li(
                    "Notice the duality between p-values and CIs: a CI does not cover 1 if and only if the p-value falls below (1 - conf. lvl.).",
                ),
            ),
        ),
        ui.tags.li(
            ui.tags.i("adj. p"),
            ": the multiple testing adjusted p-values. ",
            ui.tags.ul(
                ui.tags.li(
                    "Even with no miscalibration, some p-values can show up as significant simply due to randomness in the data. "
                    "The problem exacerbates when we search over a large number of hypotheses, and is known as p-hacking/p-fishing. "
                ),
                ui.tags.li(
                    "The adjusted p-values account for the number of hypotheses being searching over, and correct for p-hacking/p-fishing. "
                ),
                ui.tags.li(
                    "This is done via the standard ",
                    ui.HTML(
                        '<a target="_blank" href=https://www.jstor.org/stable/2346101>Benjamini-Hochberg procedure</a>; '
                    ),
                    "consult your favorite statistician on the topic.",
                ),
            ),
        ),
    ),
    ui.tags.p(
        "Notice that while the OTE is higher in Subgroup 2 (2.5 > 1.964), the width of the confidence interval is much wider. "
        "Correspondingly, the p-value of the null hypothesis of model calibration is larger for the Subgroup 2 (0.29 > 0.02). "
        "We we see stronger evidence of miscalibration for Subgroup 1, despite lower OTE. "
    ),
    id="what",
)

who_is_it_for = ui.tags.section(
    ui.tags.h1("Who is it for?"),
    ui.tags.p(
        "There are probably two groups of users:",
        ui.tags.ul(
            ui.HTML(
                "<li>"
                "People who do not code heavily: product managers, executives, analysts, etc."
                "</li>"
            ),
            ui.HTML(
                "<li>"
                "People who do code heavily, "
                "but wish to have a convenient tool and reference to correct uncertainty calculation in OTEs. "
                "</li>"
            ),
        ),
    ),
    id="who",
)


how_is_it_done = ui.tags.section(
    ui.tags.h1("How is it done?"),
    ui.HTML(
        "<p>"
        "Before reading on, it's worth noting that..."
        '<h5><i>"Confidence interval for OTE" is a misnomer</i></h5>'
        'In other words, "CI for OTE" is a phrase that does not have a statistical meaning, '
        "since the object <i>does not really exist</i>! "
        "</p>"
        "<p>"
        "Recall by definition that "
        "a confidence interval (CI) is an interval that typically contains a true <i>parameter, "
        "i.e. a fixed, unknown quantity of interest</i>, over repeated experiments. "
        "In other words, CIs are constructed for a parameter of interest as <i>interval estimates</i>; "
        "they are not, and cannot, be constructed for a random quantity. "
        "In this case, since OTE is a random quantity (the number of realized events O is random), "
        'we cannot really construct a "CI" for OTE. '
        '<p>So what is the "CI" for?</p>'
        "The interval estimate (CI) is not for OTE, but for something else that OTE itself estimates. "
        'What we call "OTE" is really a point estimate of '
        '"the (average) true probabilities" divided by '
        '"the predicted (average) probabilities" of events. '
        'We call this quantity of interest the <i>"calibration level"</i> of the model. '
        'And therefore, what we want in a "CI for OTE" is really a interval estimate of this "calibration level" as well. '
        "</p>"
    ),
    ui.HTML(
        "<p>"
        "<h5>On to the calculations...</h5>"
        "Let <code>o</code> denote the number of observed events, "
        "<code>e</code> the number of expected events, "
        "we can rerwite OTE: <code>(o/e)</code> as <code>(o/n)/(e/n)</code>. "
        "Recognizing that OTE is but the estimated probability scaled by <code>(n/e)</code>, "
        "the uncertainty of OTE can be quantified via any method that "
        "quantifies the uncertainty of the probability estimate <code>(o/n)</code>. "
        "</p>"
    ),
    ui.HTML(
        "<p>"
        "Special care has to be taken in quantifying this uncertainty, since not all methods produce CIs "
        "with correct coverage whe event counts are low. "
        "Many good choices exist, we illustrate with a edge-correct Jeffreys interval here. "
        "For a detailed discussion, see "
        '<a target="_blank" href=https://www.jstor.org/stable/2676784>Brown, Cai, and DasGupta (2001)</a>. '
        "For a discussion on methods not mentioned in the paper, see <a href=#other-methods>other methods</a> Section below. "
        "</p>"
    ),
    # ui.br(),
    ui.tags.p("The implementation is perhaps unremarkable."),
    ui.tags.pre(ui.tags.code(code_str_for_CI_OTE)),
    ui.tags.p(
        "This simple method produces an interval with the desired coverage for the quantity of interest. See ",
        ui.a(
            {
                "href": "https://github.com/teamupstart/upstart_data_analysis/blob/master/personal/zgao/OTE_CI/simulations.ipynb",
                "target": "_blank",
            },
            "simulations",
        ),
        ". ",
    ),
    id="how",
)

other_methods = ui.tags.section(
    ui.tags.h1('"What about other methods?"'),
    ui.tags.p(
        "Several other options exist for calculating uncertainty for OTEs. "
        "All of them have flaws. "
    ),
    ui.tags.h5("Bootstrap"),
    ui.HTML(
        "... is a Swiss Army Knife, if we know when and how to use it. "
        "<p>Some often forgotten facts about bootstrap make it susceptible to misuse:"
    ),
    ui.tags.ul(
        ui.HTML(
            "<li>"
            "<i>Bootstrap is only consistent asymptotically.</i> "
            "For example, when we have zero observed events, the boostrap CI would yield an interval of <code>[0, 0]</code>, "
            "which is clearly wrong for any non-zero probability events. "
            "This is problematic when we have low number of observations or small probabilities, "
            "and is a major limiting factor for when we need uncertainty "
            "estimates the most -- when data is scarce."
            "</li>"
        ),
        ui.HTML(
            "<li>"
            "<i>Bootstrap is often done wrong.</i> E.g. very few seem to remember to "
            '<a target="_blank" href=https://en.wikipedia.org/wiki/Bootstrapping_(statistics)#Deriving_confidence_intervals_from_the_bootstrap_distribution>flip the percentiles</a> '
            "when constructing boostrap CIs. "
            "Resampling with replacements is also surprisingly prone to implementation errors. "
            "A wise man once told me \"I have never seen bootstrap done right\"."
            "</li>"
        ),
    ),
    ui.tags.h5("Bayesian credible intervals"),
    ui.HTML(
        "... is certainly a valid choice for modeling and analysis. "
        "Bringing in priors is sometimes desired in order to make subjective judgments. "
        "But one must fend off some inescapable questions. "
    ),
    ui.tags.ul(
        ui.HTML(
            "<li>"
            "<i>One often needs to justify the choice of priors.</i> "
            "And this can be tricky, especially when data is scarce "
            "and results are heavily swayed by the choice of priors. "
            "(What is a good choice of prior when we have only 5 observations?) "
            "On the other hand, if the results are not sensitive to our choice of priors, "
            "we probably don't need to be Bayesian in the first place."
            "</li>"
        ),
        ui.HTML(
            "<li>"
            "<i>Bayesian credible intervals do not make valid confidence intervals.</i> "
            "If we want to avoid justifying priors to a skeptical audience, "
            'one might argue that it is "not so different from a frequentist CI". '
            "unforutnately, credible intervals constructed from most priors "
            "that we come up with do not have correct frequentist confidence coverages, especially for small probabilities. "
            "</li>"
        ),
        ui.HTML(
            "<li>"
            "<i>Even when a credible intervals almost achieve nominal frequentist converage, "
            "they can have undesirable properties.</i> "
            "Some choice of priors <i>almost</i> make valid confidence intervals. "
            "In particular, the edge-correct Jeffreys interval we demonstrated above is a "
            "modified version of credible interval with a very specific prior "
            "that comes with good frequentist coverage properties. "
            "However, the original equal-tailed Jeffreys credible interval does not contain near-zero probabilities, "
            "and therefore is not suitable for low-probability events. "
            "Edge corrections are needed. "
            "("
            'While the original Jeffreys interval is "Bayesian", the Jeffreys interval with edge correction is not. '
            'Importantly, a method is not inherently "Bayesian" or "frequentist", only their evaluations are. '
            'When we refer to a procedure as "Bayesian", what we really mean is that '
            '"it is entirely coherent in Bayesian evaluations", '
            'and not that "it uses the Baye\'s rule". '
            'Indeed, many procedures use the Baye\'s rule, but cannot be called "Bayesian methods", '
            "since they are not coherent in Bayesian evaluations."
            ")"
            "</li>"
        ),
    ),
    id="other-methods",
)

limitations = ui.tags.section(
    ui.tags.h1("Limitations"),
    ui.tags.h5("The low-count problem in other model metrics"),
    ui.tags.p(
        "One major issue the method tries to overcome is low event counts. "
        "While the calculator does the job for OTE, the low-count problem plagues "
        "all other model metrics (logloss, AUC, RMSE, etc.). "
        "And in the other metrics, I do not know of a good method of correction. "
    ),
    ui.tags.h5("Paired tests"),
    ui.tags.p(
        'The calculator only does "one-sample tests". '
        "Another common use of OTE is for model comparisons, "
        "e.g. when we want to compare the OTE of two candidate models "
        "on the same set of customers. "
        "A paired test would obviously require individual-level observed and expected events, "
        "and goes beyond the capability of the calculator. "
    ),
    ui.HTML(
        "In both cases, we do not have a better recommendation than bootstrap at the moment, but only if you have a large sample. "
        "As detailed in the <a href=#other-methods>previous section</a>, "
        "one has to be very very careful in performing bootstrap and in interpreting the results when counts are low."
    ),
    id="limitations",
)

contact = ui.tags.section(
    ui.tags.h1("Contact"),
    ui.tags.p(
        "Please reach Zheng Gao for questions and feedback on anything related to the web app. "
    ),
    id="contact",
)

about_page_content = ui.page_fluid(
    ui.row(
        ui.column(
            4,
            ui.card(
                # inputs for calculating OTE CI and p-vals
                ui.tags.a("What is it for?", href="#what"),
                ui.tags.a("Who is it for?", href="#who"),
                ui.tags.a("How is it done?", href="#how"),
                ui.tags.a("Other methods", href="#other-methods"),
                ui.tags.a("Limitations", href="#limitations"),
                ui.tags.a("Contact", href="#contact"),
            ),
            style="max-width: 350px;",
        ),
        ui.column(
            8,
            ui.card(
                what_is_it_for,
                who_is_it_for,
                how_is_it_done,
                other_methods,
                limitations,
                contact,
            ),
        ),
    ),
)
