import numpy as np

from gettsim.typing import FloatSeries


def durchschnittl_entgeltpunkte_grundrente(
    entgeltpunkte_grundrente, grundrentenbewertungszeiten
):
    """ Compute average number of entgeltpunkte earned per year of grundrentenzeiten

    Parameters
    ----------
    entgeltpunkte_grundrente
    grundrentenbewertungszeiten

    Returns
    -------

    """
    return entgeltpunkte_grundrente / grundrentenbewertungszeiten


def höchstwert(grundrentenzeiten):
    """ Maximum  number of average entgeltpunkte (per month)
    after adding bonus of entgeltpunkte

    Parameters
    ----------
    grundrentenzeiten

    Returns
    -------

    """
    return (0.0334 + 0.001389 * (grundrentenzeiten.clip(upper=420) - 396)).round(4)


def _kat1(grundrentenzeiten):
    """ Indicates that person has not enough grundrentenzeiteun to receive grundrente.
    Relevant to compute bonus of entgeltpunkte.

    Parameters
    ----------

    grundrentenzeiten

    Returns
    -------

    """
    return grundrentenzeiten < 33 * 12


def _kat2(durchschnittl_entgeltpunkte_grundrente, grundrentenzeiten, höchstwert):
    """ Indicates that person´s average monthly entgeltpunkte will be doubled bc.
    of grundrente

    Parameters
    ----------
    durchschnittl_entgeltpunkte_grundrente
    grundrentenzeiten
    höchstwert

    Returns
    -------

    """
    return (grundrentenzeiten >= 33 * 12) & (
        durchschnittl_entgeltpunkte_grundrente < (0.5 * höchstwert)
    )


def _kat3(durchschnittl_entgeltpunkte_grundrente, grundrentenzeiten, höchstwert):
    """ Indicates that person´s average monthly entgeltpunkte will be topped up
    to the höchstwert

    Parameters
    ----------
    durchschnittl_entgeltpunkte_grundrente
    grundrentenzeiten
    höchstwert

    Returns
    -------

    """
    return (
        (grundrentenzeiten >= 33 * 12)
        & (durchschnittl_entgeltpunkte_grundrente >= (0.5 * höchstwert))
        & (durchschnittl_entgeltpunkte_grundrente < höchstwert)
    )


def _kat4(durchschnittl_entgeltpunkte_grundrente, grundrentenzeiten, höchstwert):
    """ Indicates that person is not eligable to grundrente as she earned to
    many entgeltpunkte

    Parameters
    ----------
    durchschnittl_entgeltpunkte_grundrente
    grundrentenzeiten
    höchstwert

    Returns
    -------

    """
    return (grundrentenzeiten >= 33 * 12) & (
        durchschnittl_entgeltpunkte_grundrente > höchstwert
    )


def bonus_entgeltpunkte(
    _kat1, _kat2, _kat3, _kat4, durchschnittl_entgeltpunkte_grundrente, höchstwert
):
    """ Calculate additional entgeltpunkte for person resulting from grundrente

    Parameters
    ----------
    _kat1
    _kat2
    _kat3
    _kat4
    durchschnittl_entgeltpunkte_grundrente
    höchstwert

    Returns
    -------

    """
    out = _kat1.astype(float) * np.nan
    out.loc[_kat1] = 0
    out.loc[_kat2] = durchschnittl_entgeltpunkte_grundrente * (1 - 0.125)
    out.loc[_kat3] = (höchstwert - durchschnittl_entgeltpunkte_grundrente) * (1 - 0.125)
    out.loc[_kat4] = 0
    return out


def grundrente_vor_einkommensanrechnung(
    bonus_entgeltpunkte, grundrentenbewertungszeiten, rentenwert, zugangsfaktor,
):
    """ Calculate additional pensions payments resulting from grundrente,
    before taking into account other income

    Parameters
    ----------
    bonus_entgeltpunkte
    grundrentenbewertungszeiten
    rentenwert
    zugangsfaktor


    Returns
    -------

    """
    out = (
        bonus_entgeltpunkte
        * grundrentenbewertungszeiten.clip(upper=420)
        * rentenwert
        * zugangsfaktor.clip(upper=1)
    )
    return out


def grundrente1(
    grundrente_vor_einkommensanrechnung, bruttolohn_m, rente_anspr_m
) -> FloatSeries:
    """ Implement income crediting rule as defined in grundrentengesetz.
        Assumption: only other income is bruttolohn_m and rente_anspr_m.

    Parameters
    ----------
    grundrente
    bruttolohn_m
    rente_anspr_m
    Returns
    -------

    """
    out = (
        grundrente_vor_einkommensanrechnung
        - (((bruttolohn_m + rente_anspr_m).clip(upper=1600) - 1250).clip(lower=0)) * 0.6
        - ((bruttolohn_m + rente_anspr_m) - 1600).clip(lower=0)
    ).clip(lower=0)
    return out


def anzurechnende_rente(rente_anspr_m, grundrente1):
    """ implement allowance for grundsicherung im alter if person is eligable for grundrente
        allowance for wohngeld not implemented yet

    Parameters
    ----------
    keine_grundsicherung
    rente_anspr_m
    grundrente
    grundsicherung_grundrente
    grundsicherung_keine_grundrente

    Returns
    -------

    """
    gesamtrente = rente_anspr_m + grundrente1
    out = (gesamtrente - (100 + (gesamtrente - 100) * 0.3).clip(upper=0.5 * 432)).clip(
        lower=0
    )
    return out


def wohngeld_grundrente(anzurechnende_rente, grundrentenzeiten):
    return (
        (500 + 432 - anzurechnende_rente <= 432)
        & (500 + 432 - anzurechnende_rente > 0)
        & (grundrentenzeiten >= 33 * 12)
    )


def wohngeld_keine_grundrente(rente_anspr_m, bruttolohn_m, grundrentenzeiten):
    return (
        (500 + 432 - (rente_anspr_m + bruttolohn_m) <= 432)
        & (500 + 432 - (rente_anspr_m + bruttolohn_m) > 0)
        & (grundrentenzeiten < 33 * 12)
    )


def grundsicherung_grundrente(anzurechnende_rente, grundrentenzeiten):
    return (500 + 432 - anzurechnende_rente > 432) & (grundrentenzeiten >= 33 * 12)


def grundsicherung_keine_grundrente(rente_anspr_m, bruttolohn_m, grundrentenzeiten):
    return (500 + 432 - (rente_anspr_m + bruttolohn_m) > 432) & (
        grundrentenzeiten < 33 * 12
    )


def grundsicherung(
    anzurechnende_rente,
    grundsicherung_grundrente,
    grundsicherung_keine_grundrente,
    rente_anspr_m,
    grundrente1,
    bruttolohn_m,
):
    out = grundsicherung_grundrente.astype(float) * np.nan

    out.loc[grundsicherung_keine_grundrente] = (
        432 + 500 - (rente_anspr_m + grundrente1 + bruttolohn_m)
    ).clip(lower=0)

    out.loc[grundsicherung_grundrente] = ((432 + 500) - anzurechnende_rente).clip(
        lower=0
    )
    return out


def wohngeld(
    wohngeld_grundrente,
    wohngeld_keine_grundrente,
    rente_anspr_m,
    grundrente1,
    bruttolohn_m,
    anzurechnende_rente,
):

    out = wohngeld_grundrente.astype(float) * np.nan

    out.loc[wohngeld_keine_grundrente] = (
        432 + 500 - (rente_anspr_m + grundrente1 + bruttolohn_m)
    ).clip(lower=0)

    out.loc[wohngeld_grundrente] = ((432 + 500) - anzurechnende_rente).clip(lower=0)

    return out


def grundsicherung_im_alter_2020(rente_anspr_m):
    out = ((432 + 500) - rente_anspr_m).clip(lower=0)
    return out
