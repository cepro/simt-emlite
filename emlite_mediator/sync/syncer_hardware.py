from emlite_mediator.util.logging import get_logger

from typing_extensions import override

from emlite_mediator.sync.syncer_base import SyncerBase, UpdatesTuple

logger = get_logger(__name__, __file__)

class SyncerHardware(SyncerBase):
    @override
    def fetch_metrics(self) -> UpdatesTuple:
        result = self.supabase.table('meter_registry').select(
            'hardware,serial').eq("id", self.meter_id).execute()
        meter_registry_entry = result.data[0]

        # if 3 phase meter hardware fetch will fail.
        #
        # currently we have no other way to query the hardware so we check the
        # serial prefix and hardcode the hardware.
        #
        # see also ticket related to this issue on the EMOP downloader:
        #   https://cepro.unfuddle.com/a#/projects/13/tickets/by_number/390
        if meter_registry_entry['serial'].startswith('EMP1AX'):
            hardware = 'P1.ax'
        else:
            hardware = self.emlite_client.hardware()

        registry_hardware = meter_registry_entry['hardware']
        if (registry_hardware == hardware):
            logger.info("hardware unchanged - no action")
            return UpdatesTuple(None, None)

        if (registry_hardware is None and hardware is not None):
            logger.info('got new hardware', new_hardware=hardware)
        else:
            logger.warning(
                'fetched hardware and registry hardware different!',
                    new_hardware=hardware, old_hardware=registry_hardware)
        
        logger.info(
            'skipping db update for now - return no updates - TODO: sync it when changed')
                
        return UpdatesTuple(None, None)
