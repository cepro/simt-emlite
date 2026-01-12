from supabase import Client

from simt_emlite.util.supabase import as_first_item

single_phase_hardware_str_to_registry_str = {
    "6C": "C1.w",
    "6Cw": "C1.w",
    "6Bw": "B1.w",
    "3Aw": "EMA1.w",
}

three_phase_hardware_known_strings = ["P1.ax", "P1.cx", "THREE_PHASE_UNKNOWN"]


def is_twin_element(hardware: str) -> bool:
    return hardware == "C1.w"


def is_three_phase(hardware: str) -> bool:
    return hardware == "P1.ax" or hardware == "P1.cx"


def is_three_phase_lookup(supabase: Client, meter_id: str) -> bool:
    hardware = get_hardware(supabase, meter_id)
    return is_three_phase(hardware)


def get_hardware(supabase: Client, meter_id: str) -> str:
    result = (
        supabase.table("meter_registry").select("hardware").eq("id", meter_id).execute()
    )
    return as_first_item(result)["hardware"]
