def is_three_phase(hardware: str) -> bool:
    return hardware == "P1.ax"


def is_three_phase_lookup(supabase, meter_id: str) -> bool:
    result = (
        supabase.table("meter_registry").select("hardware").eq("id", meter_id).execute()
    )
    return is_three_phase(result.data[0]["hardware"])
