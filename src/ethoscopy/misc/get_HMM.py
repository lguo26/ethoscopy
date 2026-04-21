import pickle

from hmmlearn.hmm import CategoricalHMM

from ethoscopy.misc.get_tutorials import _find_pickle, _missing_files_message


def get_HMM(sex: str) -> "CategoricalHMM":
    """
    Load pre-trained Hidden Markov Models for Drosophila behavior states.

    Provides access to 4-state HMM models (Deep Sleep, Active Awake, Quiet Awake, Active Awake)
    trained separately for male and female flies.

    Args:
        sex (str): Sex of the model to load ('M' for male or 'F' for female)

    Returns:
        CategoricalHMM: Trained HMM model object from hmmlearn

    Raises:
        KeyError: If sex argument is not 'M' or 'F'
        FileNotFoundError: If HMM model file cannot be found
    """
    sex = sex.upper()
    if sex not in {"M", "F"}:
        raise KeyError('The argument for "sex" must be "M" or "F"')

    name = f"4_states_{sex}_WT.pkl"
    hmm_path = _find_pickle(name)
    if hmm_path is None:
        raise FileNotFoundError(_missing_files_message([name]))

    with open(hmm_path, "rb") as file:
        return pickle.load(file)
