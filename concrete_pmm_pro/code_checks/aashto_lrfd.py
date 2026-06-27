"""AASHTO LRFD Section 5 concrete strength helpers.

The helpers in this module keep the AASHTO LRFD 9th Edition concrete PMM
route auditable in Concrete Section Pro.  AASHTO Section 5 equations and
limits are expressed in kips, inches, and ksi; the app's solver internals stay
in mm, MPa, N, and N-mm.  Where strength-dependent thresholds are written in
ksi, these helpers convert the SI input to ksi before applying the code rule.
"""

from __future__ import annotations

from dataclasses import dataclass

from concrete_pmm_pro.core.aashto_units import mpa_to_ksi
from concrete_pmm_pro.core.models import PrestressElement, Rebar, RebarMaterial

AASHTO_ECU_STRENGTH = 0.003
AASHTO_COMPRESSION_CONTROLLED_PHI = 0.75
AASHTO_TENSION_CONTROLLED_RC_PHI = 0.90
AASHTO_TENSION_CONTROLLED_BONDED_PRESTRESS_PHI = 1.00
AASHTO_TENSION_CONTROLLED_UNBONDED_PRESTRESS_PHI = 0.90


@dataclass(frozen=True)
class AashtoPhiResult:
    phi: float
    strain_condition: str
    eps_cl: float
    eps_tl: float
    tension_phi: float
    basis: str


def aashto_alpha1(fc_MPa: float) -> float:
    """Return AASHTO LRFD rectangular stress-block alpha1 for ``fc_MPa``.

    AASHTO Section 5 defines the strength breakpoints in ksi.  The input is
    converted to ksi before applying the 10 ksi threshold and reduction rate.
    """

    if fc_MPa <= 0:
        raise ValueError("fc_MPa must be positive.")
    fc_ksi = mpa_to_ksi(fc_MPa)
    if fc_ksi <= 10.0:
        return 0.85
    return max(0.75, 0.85 - 0.02 * (fc_ksi - 10.0))


def aashto_beta1(fc_MPa: float) -> float:
    """Return AASHTO LRFD rectangular stress-block beta1 for ``fc_MPa``.

    AASHTO Section 5 defines the strength breakpoints in ksi.  The input is
    converted to ksi before applying the 4 ksi threshold and reduction rate.
    """

    if fc_MPa <= 0:
        raise ValueError("fc_MPa must be positive.")
    fc_ksi = mpa_to_ksi(fc_MPa)
    if fc_ksi <= 4.0:
        return 0.85
    return max(0.65, 0.85 - 0.05 * (fc_ksi - 4.0))


def _linear_interpolate(value: float, x0: float, y0: float, x1: float, y1: float) -> float:
    if x1 == x0:
        return y0
    ratio = (value - x0) / (x1 - x0)
    return y0 + ratio * (y1 - y0)


def aashto_compression_controlled_strain_limit(
    fy_MPa: float | None = None,
    Es_MPa: float = 200000.0,
    *,
    prestressed_reinforcement: bool = False,
) -> float:
    """Return AASHTO compression-controlled net tensile strain limit.

    Prestressing reinforcement uses 0.002.  Nonprestressed reinforcement uses
    the AASHTO ksi breakpoints for 60 ksi and 100 ksi bars.
    """

    if prestressed_reinforcement:
        return 0.002
    fy = float(fy_MPa if fy_MPa is not None else 420.0)
    Es = float(Es_MPa)
    if fy <= 0:
        raise ValueError("fy_MPa must be positive.")
    if Es <= 0:
        raise ValueError("Es_MPa must be positive.")
    fy_ksi = mpa_to_ksi(fy)
    if fy_ksi <= 60.0:
        return min(fy / Es, 0.002)
    if fy_ksi >= 100.0:
        return 0.004
    return _linear_interpolate(fy_ksi, 60.0, 0.002, 100.0, 0.004)


def aashto_tension_controlled_strain_limit(
    fy_MPa: float | None = None,
    *,
    prestressed_reinforcement: bool = False,
) -> float:
    """Return AASHTO tension-controlled net tensile strain limit."""

    if prestressed_reinforcement:
        return 0.005
    fy = float(fy_MPa if fy_MPa is not None else 420.0)
    if fy <= 0:
        raise ValueError("fy_MPa must be positive.")
    fy_ksi = mpa_to_ksi(fy)
    if fy_ksi <= 75.0:
        return 0.005
    if fy_ksi >= 100.0:
        return 0.008
    return _linear_interpolate(fy_ksi, 75.0, 0.005, 100.0, 0.008)


def aashto_phi_and_strain_condition(
    eps_t: float | None,
    *,
    fy_MPa: float | None = None,
    Es_MPa: float = 200000.0,
    prestressed_member: bool = False,
    prestressed_reinforcement_controls: bool = False,
    unbonded_prestress_controls: bool = False,
) -> AashtoPhiResult:
    """Return AASHTO LRFD φ and strain classification for axial-flexure.

    The interpolation lower bound is 0.75.  The upper bound is 0.90 for
    nonprestressed reinforced concrete, 1.00 for bonded prestressed concrete,
    and 0.90 for unbonded/debonded prestressing when explicitly controlling.
    """

    is_ps_basis = bool(prestressed_member or prestressed_reinforcement_controls or unbonded_prestress_controls)
    eps_cl = aashto_compression_controlled_strain_limit(fy_MPa, Es_MPa, prestressed_reinforcement=is_ps_basis)
    eps_tl = aashto_tension_controlled_strain_limit(fy_MPa, prestressed_reinforcement=is_ps_basis)
    if unbonded_prestress_controls:
        tension_phi = AASHTO_TENSION_CONTROLLED_UNBONDED_PRESTRESS_PHI
        basis = "AASHTO LRFD 5.5.4.2 unbonded/debonded prestressed transition"
    elif is_ps_basis:
        tension_phi = AASHTO_TENSION_CONTROLLED_BONDED_PRESTRESS_PHI
        basis = "AASHTO LRFD 5.5.4.2 bonded prestressed transition"
    else:
        tension_phi = AASHTO_TENSION_CONTROLLED_RC_PHI
        basis = "AASHTO LRFD 5.5.4.2 nonprestressed RC transition"

    eps = 0.0 if eps_t is None else max(0.0, float(eps_t))
    if eps <= eps_cl:
        return AashtoPhiResult(AASHTO_COMPRESSION_CONTROLLED_PHI, "compression-controlled", eps_cl, eps_tl, tension_phi, basis)
    if eps >= eps_tl:
        return AashtoPhiResult(tension_phi, "tension-controlled", eps_cl, eps_tl, tension_phi, basis)
    ratio = (eps - eps_cl) / (eps_tl - eps_cl)
    phi = AASHTO_COMPRESSION_CONTROLLED_PHI + ratio * (tension_phi - AASHTO_COMPRESSION_CONTROLLED_PHI)
    return AashtoPhiResult(phi, "transition", eps_cl, eps_tl, tension_phi, basis)


def _rebar_yield_strength_mpa(rebar: Rebar, default_material: RebarMaterial) -> float:
    return float(getattr(rebar, "fy_MPa", None) or getattr(rebar, "fy_mpa", None) or default_material.fy_MPa)


def _prestress_axial_strength_reference_mpa(element: PrestressElement) -> float:
    if element.fpy_mpa is not None:
        return float(element.fpy_mpa)
    if element.fpu_mpa is not None:
        return 0.90 * float(element.fpu_mpa)
    raise ValueError("Prestress element is missing both fpy_mpa and fpu_mpa.")


def aashto_nominal_po_rc_prestressed(
    fc_MPa: float,
    Ag_mm2: float,
    rebars: list[Rebar],
    rebar_material_default: RebarMaterial | None = None,
    prestress_elements: list[PrestressElement] | None = None,
) -> float:
    """Return AASHTO-style nominal concentric axial resistance in N.

    This SI helper follows the AASHTO compression-member stress coefficient
    ``kc`` basis through ``aashto_alpha1`` and subtracts modeled steel area from
    the concrete term to avoid double counting.  It uses fpy/proof stress for
    prestressing steel when available, otherwise 0.90 fpu as a conservative
    material reference.
    """

    if fc_MPa <= 0:
        raise ValueError("fc_MPa must be positive.")
    if Ag_mm2 <= 0:
        raise ValueError("Ag_mm2 must be positive.")
    default_material = rebar_material_default or RebarMaterial(name="Default", fy_MPa=390.0, Es_MPa=200000.0)
    prestress_items = prestress_elements or []
    Ast_mm2 = sum(rebar.area_mm2 for rebar in rebars)
    Aps_mm2 = sum(element.area_mm2 * element.count for element in prestress_items)
    concrete_area_mm2 = Ag_mm2 - Ast_mm2 - Aps_mm2
    if concrete_area_mm2 < 0:
        raise ValueError("Ag_mm2 minus total rebar and prestress steel area must not be negative.")

    steel_force_N = sum(_rebar_yield_strength_mpa(rebar, default_material) * rebar.area_mm2 for rebar in rebars)
    prestress_force_N = sum(_prestress_axial_strength_reference_mpa(element) * element.area_mm2 * element.count for element in prestress_items)
    return aashto_alpha1(fc_MPa) * fc_MPa * concrete_area_mm2 + steel_force_N + prestress_force_N


def aashto_column_axial_cap_factor(transverse_reinforcement: str) -> float:
    if transverse_reinforcement == "spiral":
        return 0.85
    if transverse_reinforcement == "tied":
        return 0.80
    raise ValueError("transverse_reinforcement must be tied or spiral.")


def aashto_max_phiPn(
    Po_N: float,
    *,
    transverse_reinforcement: str,
    phi_compression: float = AASHTO_COMPRESSION_CONTROLLED_PHI,
) -> float:
    """Return factored axial-resistance cap for compression members in N."""

    if Po_N < 0:
        raise ValueError("Po_N must not be negative.")
    if phi_compression <= 0:
        raise ValueError("phi_compression must be positive.")
    return aashto_column_axial_cap_factor(transverse_reinforcement) * phi_compression * Po_N
