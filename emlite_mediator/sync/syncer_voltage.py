from typing_extensions import override

from emlite_mediator.sync.syncer_base import SyncerBase, UpdatesTuple


class SyncerVoltage(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        rec = self.supabase.table('meter_registry').select(
            'serial').eq("id", self.meter_id).execute()
        is_3p = rec.data[0]['serial'].startswith('EMP1AX')

        if is_3p:
            (v1, v2, v3) = self.emlite_client.three_phase_instantaneous_voltage()
            metrics = {'3p_voltage_l1': v1,
                       '3p_voltage_l2': v2,
                       '3p_voltage_l3': v3}
        else:
            instantaneous_voltage = self.emlite_client.instantaneous_voltage()
            average_voltage = self.emlite_client.average_voltage()
            metrics = {'average_voltage': average_voltage,
                       'instantaneous_voltage': instantaneous_voltage}

        return UpdatesTuple(metrics, None)
