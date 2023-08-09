import pandas as pd


from pathlib import Path


def check_df_exists_with_no_empty_data(f: Path) -> pd.DataFrame:
    """Check if a file exists, open it as a pandas dataframe to check that it has no empty data
    Returns the dataframe for potential further investigation

    Args:
        f (Path): path to input csv file

    Returns:
        pd.DataFrame: read dataframe
    """
    assert (f).is_file()
    df = pd.read_csv(f)
    assert not df.isnull().values.any()
    return df
