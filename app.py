import dash
dash._dash_renderer._set_react_version("18.2.0")  # Forces Dash to use React 18
from dash import dcc, html, Input, Output, callback
# import dash_table
from dash_ag_grid import AgGrid
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
# import numpy as np
import config  # Import paths & configs
from utils.cache import cache  # Import cache system
import dash_mantine_components as dmc


# ✅ Load Data (Cached for Speed)
@cache.memoize()
def load_data():
    file_path = config.data_folder / "clean" / "final_data.parquet"
    return pd.read_parquet(file_path)

df = load_data()
df["year"] = pd.to_numeric(df["year"], errors="coerce").astype(int)  # Ensure integer year
df = df.sort_values("year")  # Sort in ascending order


# ✅ Variable Mapping
variable_mapping = {
    "Nightlights": "nightlights",
    "Forest Cover": "forest_cover",
    "pm25": "pm25"
}

# ✅ Get Unique States & Districts
unique_states = sorted(df["state"].unique())
unique_districts = df["district"].unique()
# Create category-to-states mapping dynamically
large_states = sorted(df[df["area_cat"] == "Large"]["state"].unique())
medium_states = sorted(df[df["area_cat"] == "Medium"]["state"].unique())
small_states = sorted(df[df["area_cat"] == "Small"]["state"].unique())
high_pop_states = sorted(df[df["pop_cat"] == "High"]["state"].unique())
medium_pop_states = sorted(df[df["pop_cat"] == "Medium"]["state"].unique())
low_pop_states = sorted(df[df["pop_cat"] == "Low"]["state"].unique())

# Required column sequence
columns_order = ["year", "state", "district", "area_cat", "pop_cat", "area", "pop11", "nightlights", "forest_cover", "pm25"]
log_columns = ["log_area", "log_pop11", "log_nightlights", "log_forest_cover", "log_pm25"]


# ✅ Initialize Dash App
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Environmental Dashboard"

# ✅ Exploration Layout
def get_explore_layout():
    return html.Div([
        # Variable Selection
        html.Div([
            html.Div([
                html.Label("X Variable:", style={"font-weight": "bold"}),
                dcc.Dropdown(
                    id="x-variable-dropdown",
                    options=[{"label": k.replace("_", " ").title(), "value": k} for k in df.columns if k not in ["state", "district", "pc11_state_id", "pc11_district_id", "pop_cat", "area_cat"]],
                    value="forest_cover",
                    clearable=False,
                    style={"width": "200px"}
                ),
            ], style={"width": "30%"}),

            html.Div([
                html.Label("Y Variable:", style={"font-weight": "bold"}),
                dcc.Dropdown(
                    id="y-variable-dropdown",
                    options=[{"label": k.replace("_", " ").title(), "value": k} for k in df.columns if k not in ["state", "district", "pc11_state_id", "pc11_district_id", "pop_cat", "area_cat", "year"]],
                    value="nightlights",
                    clearable=False,
                    style={"width": "200px"}
                ),
            ], style={"width": "30%"}),

            html.Div([
                html.Label("Bubble Size:", style={"font-weight": "bold"}),
                dcc.Dropdown(
                    id="size-variable-dropdown",
                    options=[{"label": k.replace("_", " ").title(), "value": k} for k in df.columns if k not in ["state", "district", "year", "pc11_state_id", "pc11_district_id", "pop_cat", "area_cat"]],
                    value="pop11",  # Default size variable
                    clearable=True,
                    style={"width": "200px"}
                ),
            ], style={"width": "30%"}),
        ], style={"display": "flex", "gap": "20px", "margin-bottom": "10px"}),

        # Loading Wrapper
        dcc.Loading(
            id="loading-explore-graph",
            type="circle",  # You can use "default", "circle", or "dot"
            children=[dcc.Graph(id="explore-graph")]
        ),
        # # Graph
        # dcc.Graph(id="explore-graph"),

        html.Div([
    html.Div([
        # html.Label("Select State:", style={"font-weight": "bold"}),
        dmc.Popover(
            width=300,
            position="bottom",
            withArrow=True,
            shadow="md",
            children=[
                dmc.PopoverTarget(dmc.Button("Select States")),
                dmc.PopoverDropdown(
                    dmc.MultiSelect(
                        id="state-dropdown",
                        data=[
                        {"label": "All States", "value": "All-states"},
                        {"label": "Large States", "value": "Large-states"},
                        {"label": "Medium States", "value": "Medium-states"},
                        {"label": "Small States", "value": "Small-states"},
                        {"label": "High Population States", "value": "High-pop"},
                        {"label": "Medium Population States", "value": "Medium-pop"},
                        {"label": "Low Population States", "value": "Low-pop"},
                        ] + [{"label": s, "value": s} for s in unique_states],
                        value=["Large-states"],  # Select all by default
                        searchable=True,
                        clearable=True,
                        style={"width": "100%"},
                        comboboxProps={"position": "top", "middlewares": {"flip": False, "shift": False}}
                    )
                ),
            ],
        ),
    ], style={"width": "30%"}),

    html.Div([
        # html.Label("Select District:", style={"font-weight": "bold"}),
        dmc.Popover(
            width=300,
            position="bottom",
            withArrow=True,
            shadow="md",
            children=[
                dmc.PopoverTarget(dmc.Button("Select Districts")),
                dmc.PopoverDropdown(
                    dmc.MultiSelect(
                        id="district-dropdown",
                        searchable=True,
                        clearable=True,
                        style={"width": "100%"},
                        comboboxProps={"position": "top", "middlewares": {"flip": False, "shift": False}}
                    )
                ),
            ],
        ),
    ], style={"width": "30%"}),
], style={"display": "flex", "justify-content": "space-between", "margin-top": "10px"}),
    ])



def get_compare_layout():
    return html.Div([
        dcc.Loading(
            type="default",
            children=html.Div([
                AgGrid(id="compare-grid", 
                       columnDefs=[], 
                       rowData=[],
                       defaultColDef={"resizable": True, "sortable": True, "filter": True, "minWidth": 70},  # ✅ Ensures minWidth applied
                       columnSize="sizeToFit",  
                       dashGridOptions={"pagination": True, "paginationPageSize": 10},
                       className="ag-theme-alpine")
            ])
        ),
        html.Div([
            dcc.Checklist(
                id="show-log-values",
                options=[{"label": "Show Log Values", "value": "show"}],
                value=[]
            )
        ], style={"display": "flex", "gap": "10px"})
    ])





# Layout
app.layout = dmc.MantineProvider(
    theme={"colorScheme": "light",
           "fontFamily": "Lora, serif"},
    children=[
        dmc.Paper(
            shadow="xs",
            radius="md",
            p="md",
            style={"backgroundColor": "#FAE3E3"},  # Soft pastel background
            children=[
                dmc.Tabs(
                    id="main-tabs",
                    value="explore",
                    variant="pills",  # Soft pill-styled tabs
                    color="gray",
                    children=[
                        dmc.TabsList(
                            grow=True,
                            children=[
                                dmc.TabsTab("📊 Graphical Exploration", value="explore", style={"fontWeight": "bold"}),
                                dmc.TabsTab("🔄 Data and Regressions", value="compare", style={"fontWeight": "bold"}),
                            ],
                        ),
                    ],
                ),
                dmc.Space(h=10),  # Adds spacing below tabs
                dmc.Container(
                    html.Div(id="tabs-content"),
                    fluid=True,
                    style={
                        "backgroundColor": "#FFF5F5",  # Very Soft Pinkish-Red
                        "borderRadius": "10px",
                        "padding": "20px",
                        "boxShadow": "0px 4px 10px rgba(0,0,0,0.1)",
                    },
                ),
            ],
        ),
    ],
)


# ✅ Callback to update main tab content
@app.callback(
    Output("tabs-content", "children"),
    Input("main-tabs", "value")
)
def update_main_tab(selected_tab):
    # print(f"Switched to tab: {selected_tab}")
    try:
        if selected_tab == "compare":
            return get_compare_layout()
        elif selected_tab == "explore":
            return get_explore_layout()
        else:
            return html.Div("Invalid tab selected")
    except Exception as e:
        print(f"Error in update_main_tab: {e}")
        return html.Div(f"Error: {e}")

# # ✅ Callback to load AgGrid only when "compare" tab is active
# @app.callback(
#     Output("compare-grid-container", "children"),
#     Input("main-tabs", "value")
# )
# def update_compare_layout(tab_value):
#     if tab_value == "compare":
#         return AgGrid(
#             id="compare-grid",
#             columnDefs=[{"headerName": col, "field": col} for col in df.columns],
#             rowData=df.to_dict("records"),
#             defaultColDef={"sortable": True, "filter": True, "resizable": True},
#             pagination=True,
#             paginationPageSize=25,
#         )
#     return None  # Ensures the grid is hidden when switching tabs



# def get_compare_layout():
#     return html.Div([
#         # AG Grid table
#         AgGrid(
#             id="compare-grid",
#             columnDefs=[],  # Will be dynamically set in callback
#             rowData=[],  # Will be updated in callback
#             defaultColDef={"sortable": True, "filter": True, "resizable": True},
#             pagination=True,  # Enable pagination
#             paginationPageSize=25,  # Default page size
#         ),

#         # Grid for log checkbox (left) and rows-per-page dropdown (right)
#         dmc.Grid(
#             gutter="xs",
#             children=[
#                 dmc.Col(
#                     dcc.Checklist(
#                         id="show-log-values",
#                         options=[{"label": " Show Log Values", "value": "on"}],
#                         value=[],  # Default unchecked
#                         inline=True
#                     ),
#                     span=6,  # Takes half the width
#                     style={"textAlign": "left"}
#                 ),
#                 dmc.Col(
#                     dcc.Dropdown(
#                         id="rows-per-page",
#                         options=[{"label": str(n), "value": n} for n in [10, 25, 50, 100]],
#                         value=25,
#                         clearable=False
#                     ),
#                     span=6,  # Takes half the width
#                     style={"textAlign": "right"}
#                 ),
#             ]
#         )
#     ])


# # ✅ Update Main Tabs
# @app.callback(
#     Output("tabs-content", "children"),
#     Input("main-tabs", "value")
# )
# def update_main_tab(tab):
#     print(f"Switched to tab: {tab}")  # Debugging statement
#     return get_explore_layout() if tab == "explore" else get_compare_layout()

# # ✅ Render AG Grid only when "compare" tab is active
# @callback(
#     Output("compare-grid-container", "children"),
#     Input("main-tabs", "value"),
#     prevent_initial_call=True
# )
# def render_aggrid(tab):
#     if tab != "compare":
#         return []  # No grid if tab isn't "compare"
    
#     # Return AgGrid component when tab is "compare"
#     return AgGrid(
#         id="compare-grid",
#         columnDefs=[],  # Will be set dynamically
#         rowData=[],  # Will be updated dynamically
#         defaultColDef={"sortable": True, "filter": True, "resizable": True},
#         pagination=True,
#         paginationPageSize=25,  # Default
#     )
    
# ✅ Update Districts Based on Selected States
@app.callback(
    [Output("district-dropdown", "data"),
     Output("district-dropdown", "value"),
     Output("state-dropdown", "value")],
    Input("state-dropdown", "value")
)
def update_district_options(selected_states):
    if not selected_states:
        return [], [], []

    # Expand categories into actual states
    area_mapping = {
        "Large-states": large_states,
        "Medium-states": medium_states,
        "Small-states": small_states,
    }
    pop_mapping = {
        "High-pop": high_pop_states,
        "Medium-pop": medium_pop_states,
        "Low-pop": low_pop_states,
    }

    all_mapping ={
        "All-states": unique_states
    }

    # Expand selected categories into actual states
    expanded_states = set()
    for state in selected_states:
        if state in area_mapping:
            expanded_states.update(area_mapping[state])
        elif state in pop_mapping:
            expanded_states.update(pop_mapping[state])
        elif state in all_mapping:
            expanded_states.update(all_mapping[state])
        else:
            expanded_states.add(state)  # Add actual states

    # Ensure only states remain in the final selection (remove category labels)
    modified_selection = sorted(list(expanded_states))

    # Get districts based on the final expanded state list
    filtered_districts = (
        df[df["state"].isin(expanded_states)]
        .sort_values(["state", "district"])  # Sort first by state, then by district
        ["district"]
        .unique()
    )
    district_options = [{"label": d, "value": d} for d in filtered_districts]

    return district_options, filtered_districts, modified_selection





@app.callback(
    Output("explore-graph", "figure"),
    [Input("x-variable-dropdown", "value"),
     Input("y-variable-dropdown", "value"),
     Input("size-variable-dropdown", "value"),
     Input("state-dropdown", "value"),
     Input("district-dropdown", "value")]
)
def update_explore_graph(x_var, y_var, size_var, selected_states, selected_districts):
    selected_states = selected_states or []
    selected_districts = selected_districts or []



    if isinstance(selected_states, str):
        selected_states = [selected_states]
    if isinstance(selected_districts, str):
        selected_districts = [selected_districts]
    
    # Expand categories to actual states
    area_mapping = {
        "Large-states": large_states,
        "Medium-states": medium_states,
        "Small-states": small_states,
    }

    pop_mapping = {
        "High-pop": high_pop_states,
        "Medium-pop": medium_pop_states,
        "Low-pop": low_pop_states,
    }

    expanded_states = set()
    for state in selected_states:
        if state in area_mapping:
            expanded_states.update(area_mapping[state])
        elif state in pop_mapping:
            expanded_states.update(pop_mapping[state])
        else:
            expanded_states.add(state)  # It's an individual state
            

    # # Get districts based on expanded states
    # filtered_districts = sorted(df[df["state"].isin(expanded_states)]["district"].unique())

    df_filtered = df[df["state"].isin(expanded_states)]
    # df_filtered["state"] = pd.Categorical(df_filtered["state"], categories=sorted(df_filtered["state"].unique()), ordered=True)

    if selected_districts:
        df_filtered = df_filtered[df_filtered["district"].isin(selected_districts)]

    if df_filtered.empty:
        return px.scatter(title="No data available for selected filters")

    # # Apply log transformation if selected
    # if log_option == "log":
    #     df_filtered = df_filtered.copy()
    #     df_filtered[x_var] = df_filtered[x_var].replace(0, np.nan)
    #     df_filtered[y_var] = df_filtered[y_var].replace(0, np.nan)
    #     df_filtered[x_var] = np.log1p(df_filtered[x_var])
    #     df_filtered[y_var] = np.log1p(df_filtered[y_var])

    # Define margins for better visibility
    x_margin = (df_filtered[x_var].max() - df_filtered[x_var].min()) * 0.05  # 5% of the range
    y_margin = (df_filtered[y_var].max() - df_filtered[y_var].min()) * 0.05  # 5% of the range
    # Format the numerical columns to two decimal places for hover data
    df_filtered["x_var_formatted"] = df_filtered[x_var].apply(lambda x: f"{x:.2f}" if isinstance(x, float) and not x.is_integer() else f"{int(x)}")
    df_filtered["y_var_formatted"] = df_filtered[y_var].apply(lambda x: f"{x:.2f}" if isinstance(x, float) and not x.is_integer() else f"{int(x)}")
    if size_var:
        df_filtered["size_var_formatted"] = df_filtered[size_var].apply(
            lambda x: f"{x:.2f}" if isinstance(x, float) and not x.is_integer() else f"{int(x)}"
        )
    else:
        df_filtered["size_var_formatted"] = None  # Or df_filtered["size_var_formatted"] = ""

    df_filtered = df_filtered.sort_values(by=["year", "state"])  # ✅ Sort by year, then state






    
    # Create the plot with formatted hover data and custom labels
    fig = px.scatter(
        df_filtered, 
        x=x_var, 
        y=y_var, 
        animation_frame="year",
        animation_group="pc11_district_id",
        color="state",
        opacity=0.7,  # Adjust opacity for better visibility
        # color_discrete_sequence=px.colors.qualitative.Plotly,
        # color_palette = px.colors.qualitative.Dark24 + px.colors.qualitative.Light24,
        # color_discrete_map={state: color for state, color in zip(sorted(df_filtered["state"].unique()), px.colors.qualitative.Dark24 + px.colors.qualitative.Light24)},
        color_discrete_map={state: color for state, color in zip(sorted(df_filtered["state"].unique()), px.colors.qualitative.Prism)},
        size=size_var if size_var else None,  # Conditionally include size
        hover_data={
            "district": True, 
            "state": True, 
            "year": False,
            x_var: False,
            y_var: False,
            size_var: False if size_var else None,  # Ensure it doesn’t appear in hover data if blank
            "x_var_formatted": True, 
            "y_var_formatted": True, 
            "size_var_formatted": True if size_var else False,
        },
        range_x=[df_filtered[x_var].min() - x_margin, df_filtered[x_var].max() + x_margin],
        range_y=[df_filtered[y_var].min() - y_margin, df_filtered[y_var].max() + y_margin],
        labels={x_var: x_var.replace("_", " ").title(), 
                y_var: y_var.replace("_", " ").title(), 
                "year": "Year", 
                "x_var_formatted": f"{x_var.replace('_', ' ').title()}", 
                "y_var_formatted": f"{y_var.replace('_', ' ').title()}"} | ({"size_var_formatted": f"{size_var.replace('_', ' ').title()}"} if size_var else {}),
        title=f"{y_var.replace('_', ' ').title()} vs {x_var.replace('_', ' ').title()} Over Time",
        render_mode="svg"
    )

    # # ❌ Hide x-axis labels but keep range_x applied
    # if x_var == "year":
    #     fig.update_xaxes(
    #         showticklabels=False,  # Hides x-axis labels
    #         title=None,            # Removes title
    #         showgrid=True,         # Keeps grid visible for context
    #         zeroline=False         # Hides zero line
    #     )


    fig.update_layout(coloraxis_colorbar_title=y_var)
    return fig


@app.callback(
    Output("compare-grid", "columnDefs"),
    Output("compare-grid", "rowData"),
    Output("compare-grid", "key"),  # ✅ Forces re-render on column changes
    Input("show-log-values", "value"),
)
def update_table(log_toggle):
    log_enabled = "show" in log_toggle  # ✅ Convert list to boolean

    # Ensure correct column selection
    display_columns = columns_order + (log_columns if log_enabled else [])
    valid_columns = [col for col in display_columns if col in df.columns]

    # Sort and filter dataframe
    df_sorted1 = df.dropna(subset=["year", "state", "district"]).sort_values(["year", "state", "district"])[valid_columns]
    # ✅ Format float columns to 2 decimal places using .map()
    float_cols = df_sorted1.select_dtypes(include=["float"]).columns  # Identify float columns
    for col in float_cols:
        df_sorted1[col] = df_sorted1[col].map(lambda x: round(x, 2) if pd.notna(x) else x)

    rowData = df_sorted1.to_dict("records")
    # print(df_sorted1.head())

    # Explicitly set column definitions
    columnDefs = [
        {
            "headerName": col.replace("_", " ").title(),
            "field": col,
            "pinned": "left" if col in ["year", "state", "district"] else None,
            "minWidth": 70,  # ✅ Ensures all columns have minWidth=50
            "resizable": True,
            "sortable": True,
            "filter": True
        }
        for col in valid_columns
    ]

    return columnDefs, rowData, str(log_enabled)  # ✅ `key` ensures AgGrid refreshes properly



# ✅ Run App
if __name__ == "__main__":
    app.run_server(debug=True)
