import pandas as pd
import numpy as np

from shiny import App, render, ui, reactive

from constants import _CONF_LVL_COL, _CI_COL, _P_VAL_COL, _MULT_ADJ_P_VAL_COL
from stats import ci_ote, calculate_p_value, p_val_to_str, BH_adjusted_pval
from about import about_page_content

app_ui = ui.page_navbar(
    ui.nav_panel(
        "Calculator",
        ui.page_fluid(
            ui.row(
                ui.column(
                    4,
                    ui.card(
                        # inputs for calculating OTE CI and p-vals
                        ui.tooltip(
                            ui.input_numeric(
                                "n_observations",
                                label="Number of samples (n)",
                                value=10,
                                min=1,
                            ),
                            "The total number of observations, integers only",
                            id="n_input_tooltip",
                            placement="right",
                        ),
                        ui.output_ui("observed_expected_inputs"),
                        ui.tooltip(
                            ui.input_select(
                                "confidence_level",
                                "Confidence level (1-alpha)",
                                {
                                    "0.995": "99.5%",
                                    "0.99": "99.0%",
                                    "0.95": "95.0%",
                                    "0.90": "90.0%",
                                },
                                selected="0.95",
                            ),
                            "The confidence level of the CI",
                            id="confidence_level_tooltip",
                            placement="right",
                        ),
                        # action buttons
                        ui.tooltip(
                            ui.input_action_button(
                                "calculate_button",
                                "Calculate",
                                style="width: 100%; max-width: 300px;",
                            ),
                            "Calculate CI and p-value based on the inputs above.\nAdd results top of the results table.",
                            id="calculate_button_tooltip",
                        ),
                        ui.tooltip(
                            ui.input_action_button(
                                "undo_button",
                                "Undo",
                                style="width: 100%; max-width: 300px;",
                            ),
                            "Remove the previous result from the results table (LIFO)",
                            id="undo_button_tooltip",
                            placement="right",
                        ),
                        ui.tooltip(
                            ui.input_action_button(
                                "clear_button",
                                "Clear",
                                style="width: 100%; max-width: 300px;",
                            ),
                            "Clear the results table",
                            id="clear_button_tooltip",
                            placement="right",
                        ),
                    ),
                    style="max-width: 350px;",
                ),
                # Output in the column on the right
                ui.column(
                    8,
                    ui.card(
                        ui.output_data_frame("show_results_df"),
                    ),
                ),
            ),
        ),
    ),
    ui.nav_panel(
        "About",
        about_page_content,
    ),
    title='"Calibration (OTE) CI"',
    id="page",
)

EMPTY_RESULTS_DF = pd.DataFrame(
    {
        "n": [],
        "o": [],
        "e": [],
        "OTE": [],
        _CONF_LVL_COL: [],
        _CI_COL: [],
        _P_VAL_COL: [],
    }
)

EMPTY_RESULTS_DISPLAY_DF = EMPTY_RESULTS_DF.copy()
EMPTY_RESULTS_DISPLAY_DF[_MULT_ADJ_P_VAL_COL] = []


def server(input, output, session):

    results_df = reactive.value(EMPTY_RESULTS_DF.copy())
    results_df_to_display = reactive.value(EMPTY_RESULTS_DISPLAY_DF.copy())

    @render.ui
    def observed_expected_inputs():
        n_observed_max = input.n_observations()
        n_expected_max = input.n_observations()
        return ui.TagList(
            ui.tooltip(
                ui.input_numeric(
                    "n_observed",
                    "Number of observed events (o):",
                    value=np.nan,
                    min=0,
                    max=n_observed_max,
                    step=0.1,
                ),
                "The total number of observed events, fractional values allowed",
                id="o_input_tooltip",
                placement="right",
            ),
            ui.tooltip(
                ui.input_numeric(
                    "n_expected",
                    "Number of expected events (e):",
                    value=np.nan,
                    min=0,
                    max=n_expected_max,
                    step=0.1,
                ),
                "The total number of expected events, fractional values allowed",
                id="e_input_tooltip",
                placement="right",
            ),
        )

    @reactive.effect
    @reactive.event(input.calculate_button)
    def update_results_df():
        n, o, e = input.n_observations(), input.n_observed(), input.n_expected()
        cl = float(input.confidence_level())
        results_df_val = results_df.get()

        is_n_valid = isinstance(n, int) and (n > 0)
        is_o_valid = isinstance(o, (int, float)) and (o <= n) and (o >= 0)
        is_e_valid = isinstance(e, (int, float)) and (e <= n) and (e > 0)

        if is_n_valid and is_o_valid and is_e_valid:
            with ui.Progress(min=1, max=4) as progress_bar:
                progress_bar.set(
                    message="Calculation in progress", detail="This may take a while..."
                )
                ote = np.round(o / e, 3)
                progress_bar.set(1, message="Calculating CI...")
                ci = str(tuple(np.round(ci_ote(n, o, e, cl), 2)))
                progress_bar.set(
                    2,
                    message="Calculating p value...",
                    detail="This may take a while...",
                )
                p_val = calculate_p_value(n, o, e)
                progress_bar.set(4, message="Updating table...")
                results_df_val.loc[-1] = [
                    n,
                    o,
                    e,
                    ote,
                    cl,
                    ci,
                    p_val,
                ]
                results_df_val.index = results_df_val.index + 1  # shifting index
                results_df_val = results_df_val.sort_index()
        else:
            m = ""
            if not is_n_valid:
                m = "Invalid number of samples (n). Number must be a positive integer.\n"
            elif not is_o_valid:
                m = "Invalid number of observed events (o). Number must be a non-negative number between 0 and n.\n"
            elif not is_e_valid:
                m = "Invalid number of expected events (e). Number must be a positive number between 0 and n.\n"
            error_prompt = ui.modal(
                m,
                title="Check input values",
                easy_close=True,
                footer=None,
            )
            ui.modal_show(error_prompt)
        results_df.set(results_df_val)
        return

    @reactive.effect
    @reactive.event(input.clear_button)
    def clear_results_df():
        results_df.set(EMPTY_RESULTS_DF.copy())
        return

    @reactive.effect
    @reactive.event(input.undo_button)
    def remove_entry_from_results_df():
        results_df_val = results_df.get()
        if len(results_df_val) > 0:
            results_df_val = results_df_val.iloc[1:]
            results_df_val = results_df_val.reset_index(drop=True)
            results_df.set(results_df_val)
        return

    @render.data_frame
    def show_results_df():
        """
        Take raw values of the results dataframe, and apply formatting
        """
        results_df_val = results_df.get()
        results_df_to_display_val = results_df_val.copy()
        # calculate adjusted p-values
        adj_p_vals = BH_adjusted_pval(results_df_to_display_val[_P_VAL_COL])
        results_df_to_display_val[_MULT_ADJ_P_VAL_COL] = adj_p_vals
        # format p-values
        results_df_to_display_val[_P_VAL_COL] = (
            results_df_to_display_val[_P_VAL_COL].astype(float).apply(p_val_to_str)
        )
        results_df_to_display_val[_MULT_ADJ_P_VAL_COL] = (
            results_df_to_display_val[_MULT_ADJ_P_VAL_COL]
            .astype(float)
            .apply(p_val_to_str)
        )
        results_df_to_display.set(results_df_to_display_val)
        return render.DataTable(results_df_to_display())


app = App(app_ui, server)
