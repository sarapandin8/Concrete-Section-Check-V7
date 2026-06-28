"""Code-check helper functions for future design modules."""

from concrete_pmm_pro.code_checks.aci318 import (
    aci_beta1,
    aci_column_axial_cap_factor,
    aci_max_phiPn,
    nominal_po_rc,
    nominal_po_rc_prestressed,
    prestress_axial_strength_reference_mpa,
)
from concrete_pmm_pro.code_checks.phi_factor import aci_phi_and_strain_condition, aci_phi_from_tensile_strain
from concrete_pmm_pro.code_checks.aashto_lrfd import (
    AASHTO_ECU_STRENGTH,
    AASHTO_SHEAR_PHI,
    AashtoShearResult,
    aashto_alpha1,
    aashto_beta1,
    aashto_compression_controlled_strain_limit,
    aashto_max_phiPn,
    aashto_nominal_po_rc_prestressed,
    aashto_phi_and_strain_condition,
    aashto_min_transverse_avs_mm2_per_mm,
    aashto_shear_smax_mm,
    aashto_simplified_shear_result,
    aashto_tension_controlled_strain_limit,
)

__all__ = [
    "aci_beta1",
    "aci_column_axial_cap_factor",
    "aci_max_phiPn",
    "aci_phi_and_strain_condition",
    "aci_phi_from_tensile_strain",
    "AASHTO_ECU_STRENGTH",
    "AASHTO_SHEAR_PHI",
    "AashtoShearResult",
    "aashto_alpha1",
    "aashto_beta1",
    "aashto_compression_controlled_strain_limit",
    "aashto_max_phiPn",
    "aashto_nominal_po_rc_prestressed",
    "aashto_phi_and_strain_condition",
    "aashto_min_transverse_avs_mm2_per_mm",
    "aashto_shear_smax_mm",
    "aashto_simplified_shear_result",
    "aashto_tension_controlled_strain_limit",
    "nominal_po_rc",
    "nominal_po_rc_prestressed",
    "prestress_axial_strength_reference_mpa",
]
