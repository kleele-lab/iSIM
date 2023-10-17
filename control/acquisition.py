from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import useq

import useq

class iSIMAcquisition(dict):
    """Central dict that holds all data necessary to run the iSIM.

    Different components can request views into the dict that are necessart for them to function.
    It includes information for the NIDAQ, pymmcore-plus etc.
    """
    def __init__(
        self,
        laser_powers: dict = {'488': 0.2, '561': 0.5},
        use_filters: bool = False,
        relative_z: float = 0.0,
        axis_order: str = "tpgcz",
        time_plan: dict = None,
        channels: (dict) = ({"config": "488"}, ),
        z_plan: dict = None,
        grid_plan: dict = None,

                 ):
        super().__init__()
        self['laser_powers'] = laser_powers
        self['use_filters'] = use_filters
        self['relative_z'] = relative_z
        self['acquisition'] = {}
        self['acquisition']['axis_order'] = axis_order
        self['acquisition']['channels'] = channels
        self['acquisition']['z_plan'] = z_plan
        self['acquisition']['time_plan'] = time_plan
        self['acquisition']['grid_plan'] = grid_plan

        self.set_defaults_grid_plan()

    def to_useq_seq(self):
        return useq.MDASequence(**self["acquisition"])

    def acquisition_settings_from_useq(self, seq: useq.MDASequence):
        self["acquisition"] = seq.model_dump()

    def set_defaults_grid_plan(self):
        self['acquisition']['grid_plan']['fov_width'] = 118
        self['acquisition']['grid_plan']['fov_height'] = 118
        self['acquisition']['grid_plan']['overlap'] = (0.1, 0.1)
        self['acquisition']['grid_plan']['mode'] = "row_wise_snake"
        self['acquisition']['grid_plan']['relative_to'] = 'center'



if __name__ == "__main__":
    import useq
    from useq import MDASequence
    seq = MDASequence(time_plan = {"interval": 0.2, "loops": 20},
                      z_plan = {"top": 50, "bottom": 0, "step": 0, "go_up": True},
                      grid_plan={"rows": 2, "columns": 2},
                      stage_positions=[(0,0,1), (1000,1000,1)])
    acq = iSIMAcquisition()
    # acq.acquisition_settings_from_useq(seq)
    print(acq)
    print(seq.model_dump())
    print("\n\n\n")
    print(acq.to_useq_seq())


# Full dict for a MDASequence
# autofocus_plan: null
# axis_order:
# - t
# - p
# - g
# - z
# - c
# channels:
# - acquire_every: 1
#   camera: null
#   config: Cy5
#   do_stack: true
#   exposure: 100.0
#   group: Channel
#   z_offset: 0.0
# - acquire_every: 1
#   camera: null
#   config: DAPI
#   do_stack: true
#   exposure: 100.0
#   group: Channel
#   z_offset: 0.0
# grid_plan:
#   columns: 1
#   fov_height: 512.0
#   fov_width: 512.0
#   mode: row_wise_snake
#   overlap:
#   - 0.0
#   - 0.0
#   relative_to: center
#   rows: 1
# keep_shutter_open_across: []
# metadata:
#   pymmcore_widgets:
#     version: 0.5.3
# stage_positions:
# - name: null
#   sequence: null
#   x: 0.0
#   y: 0.0
#   z: 0.0
# time_plan:
#   interval: 0:00:01
#   loops: 1
#   prioritize_duration: false
# z_plan:
#   bottom: 0.0
#   go_up: true
#   step: 1.0
#   top: 20.0