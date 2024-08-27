from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple, Optional

from data_to_paper.base_steps import BaseCodeProductsGPT
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.llm_coding_utils.df_to_figure import ALLOWED_PLOT_KINDS
from data_to_paper.research_types.hypothesis_testing.cast import ScientificAgent
from data_to_paper.research_types.hypothesis_testing.scientific_products import ScientificProducts, get_code_name, \
    get_code_agent
from data_to_paper.utils import dedent_triple_quote_str
from data_to_paper.utils.nice_list import NiceList


@dataclass
class BaseScientificCodeProductsHandler:
    code_step: str = ''  # "data_analysis", "data_exploration", "data_processing"
    products: ScientificProducts = None
    assistant_agent: ScientificAgent = ScientificAgent.Performer
    user_agent: ScientificAgent = None

    actions_and_conversations: ActionsAndConversations = field(default_factory=ActionsAndConversations)
    code_name: str = None
    conversation_name: str = None

    def __post_init__(self):
        if self.code_name is None:
            self.code_name = get_code_name(self.code_step)
        if self.conversation_name is None:
            self.conversation_name = f'{self.code_name} Code'
        if self.user_agent is None:
            self.user_agent = get_code_agent(self.code_step)


@dataclass
class BaseScientificCodeProductsGPT(BaseScientificCodeProductsHandler, BaseCodeProductsGPT):
    allow_data_files_from_sections: Tuple[Optional[str]] = (None, )  # None for the raw data files, () for no data files
    background_product_fields: Tuple[str, ...] = ('all_file_descriptions', 'research_goal')

    def __post_init__(self):
        BaseScientificCodeProductsHandler.__post_init__(self)
        BaseCodeProductsGPT.__post_init__(self)

    @property
    def files_available_from_prior_stages(self) -> NiceList[str]:
        files = NiceList([], wrap_with='"', separator='\n')
        for section in self.allow_data_files_from_sections:
            if section is None:
                continue
            if section in self.products.codes_and_outputs:
                files += \
                    self.products.codes_and_outputs[section].created_files.get_created_files_available_for_next_steps()
        return files

    @property
    def data_filenames(self) -> NiceList[str]:
        return NiceList(self.raw_data_filenames + self.files_available_from_prior_stages,
                        wrap_with='"', prefix='\n', separator='\n', suffix='\n')

    @property
    def list_additional_data_files_if_any(self) -> str:
        if len(self.files_available_from_prior_stages) == 0:
            return ''
        return f'\nOr you can also use the processed files created above by the data processing code:\n' \
               f'```\n' \
               f'{self.files_available_from_prior_stages}' \
               f'```\n' \
               f'Important: use the correct version of the data to perform each of the steps. For example, ' \
               f'for descriptive statistics use the original data, for model building use the processed data.'

    @property
    def raw_data_filenames(self) -> NiceList[str]:
        if None in self.allow_data_files_from_sections:
            return NiceList(self.products.data_file_descriptions.get_data_filenames(),
                            wrap_with='"',
                            prefix='{} data file[s]: ')
        return NiceList([], wrap_with='"', prefix='No data files.')

    @property
    def data_folder(self) -> Optional[Path]:
        return Path(self.products.data_file_descriptions.data_folder)


class BaseTableCodeProductsGPT(BaseScientificCodeProductsGPT):
    df_to_latex_extra_vars: str = dedent_triple_quote_str('''
        note: str = None, 
        glossary: Dict[Any, str] = None,
        ''', indent=8)

    df_to_latex_extra_vars_explain: str = dedent_triple_quote_str('''
        `note` (str): Note to be added below the table caption.
        `glossary` (Dict[Any, str]): Glossary for the table.
        ''', indent=4)

    df_to_latex_doc: str = dedent_triple_quote_str('''
        def df_to_latex(df, 
                filename: str, caption: str,
        {df_to_latex_extra_vars}\t
            ):
            """
            Saves a DataFrame `df` and creates a LaTeX table.
            `filename`, `caption`: as in `df.to_latex`.
        {df_to_latex_extra_vars_explain}\t
            """
        ''')

    allowed_plot_kinds: NiceList[str] = NiceList(ALLOWED_PLOT_KINDS, wrap_with="'", separator=', ')

    df_to_figure_extra_vars: str = dedent_triple_quote_str('''
        xlabel: str = None, ylabel: str = None,
        note: str = None, glossary: Dict[Any, str] = None,
        ''', indent=8)

    df_to_figure_extra_vars_explain: str = dedent_triple_quote_str('''
        `xlabel` (str): Label for the x-axis.
        `ylabel` (str): Label for the y-axis.
        `note` (str): Note to be added below the figure caption.
        `glossary` (Dict[Any, str]): Glossary for the figure.
        ''', indent=4)

    df_to_figure_doc: str = dedent_triple_quote_str('''
        ColumnChoice = Union[str, NoneType, Iterable[str]]

        def df_to_figure(
                df, filename: str, caption: str,
                x: Optional[str] = None, y: ColumnChoice = None, 
                kind: str = 'line',
                logx: bool = False, logy: bool = False,
                yerr: ColumnChoice = None,
                y_ci: ColumnChoice = None,
                y_p_value: ColumnChoice = None,
        {df_to_figure_extra_vars}\t
            ):
            """
            Save a DataFrame `df` and create a LaTeX figure.
            Parameters, for LaTex embedding of the figure:
            `df`, `filename`, `caption`

            Parameters for df.plot():
            `x` (optional, str): Column name for x-axis (index by default).
            `y` (ColumnChoice): Column name(s) for y-axis.
            `kind` (str): {allowed_plot_kinds}.
            `logx` / `logy` (bool): log scale for x/y axis.
        {df_to_figure_extra_vars_explain}\t

            Errorbars can be specified with either `yerr` (when indicating deviations from nominal) or \t
        `y_ci` (when indicating confidence intervals, flanking the nominal):
            * `yerr` (ColumnChoice): Column name(s) for y error bars. In each designated column, \t
        all values should be either:
                - scalar denoting symmetric error bars, spanning (df[y]-df[yerr], df[y]+df[yerr])
                - 2-element tuple (bottom, top) denoting asymmetric error bars, \t
        spanning (df[y]-df[yerr][0], df[y]+df[yerr][1]) 
            * `y_ci` (ColumnChoice): Column name(s) for y confidence intervals.  
               -  The values in each such column should be a 2-element tuple (lower, upper).
                  errorbar spanning: (df[y_ci][0], df[y_ci][1])

            `y_p_value` (ColumnChoice): Column name(s) for numeric p-values, which will be automatically \t
        automatically plotted as stars ('***', '**', '*', 'ns') above the error bars.   

            If provided, the length of `yerr`, `y_ci`, and `y_p_value` should be the same as of `y`.

            Example:
            Suppose, we have:

            df_lin_reg_longevity = pd.DataFrame({
                'adjusted_coef': [0.4, ...], 'adjusted_coef_ci': [(0.35, 0.47), ...], \t
        'adjusted_coef_pval': [0.012, ...],   
                'unadjusted_coef': [0.2, ...], 'unadjusted_coef_ci': [(0.16, 0.23), ...], \t
        'unadjusted_coef_pval': [0.0001, ...],
            }, index=['var1', ...])

            then:
            df_to_figure(df_lin_reg_longevity, 'df_lin_reg_longevity', caption='Coefficients of ...', kind='bar',  
                y=['adjusted_coef', 'unadjusted_coef'], 
                y_ci=['adjusted_coef_ci', 'unadjusted_coef_ci'], 
                y_p_value=['adjusted_coef_pval', 'unadjusted_coef_pval'])
            """
        ''')
