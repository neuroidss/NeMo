# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytorch_lightning as pl

from nemo.collections.common.callbacks import LogEpochTimeCallback
from nemo.collections.tts.models.radtts import RadTTSModel
from nemo.core.config import hydra_runner
from nemo.utils import logging
from nemo.utils.exp_manager import exp_manager


def prepare_model_weights(model, unfreeze_modules):
    if unfreeze_modules != 'all':
        model.freeze()  # freeze everything
        logging.info("module frozen")
        if 'dur' in unfreeze_modules and hasattr(model.model, 'dur_pred_layer'):
            logging.info("Training duration prediction")
            model.model.dur_pred_layer.unfreeze()
        if 'f0' in unfreeze_modules and hasattr(model.model, 'f0_pred_module'):
            logging.info("Training F0 prediction")
            model.model.f0_pred_module.unfreeze()
        if 'energy' in unfreeze_modules and hasattr(model.model, 'energy_pred_module'):
            logging.info("Training energy prediction")
            model.model.energy_pred_module.unfreeze()
        if 'vpred' in unfreeze_modules and hasattr(model.model, 'v_pred_module'):
            logging.info("Training voiced prediction")
            model.model.v_pred_module.unfreeze()
            if hasattr(model, 'v_embeddings'):
                logging.info("Training voiced embeddings")
                model.model.v_embeddings.unfreeze()
        if 'unvbias' in unfreeze_modules and hasattr(model.model, 'unvoiced_bias_module'):
            logging.info("Training unvoiced bias")
            model.model.unvoiced_bias_module.unfreeze()
        else:
            logging.info("Model does not have the specified attribute.")
    else:
        logging.info("Training everything")


@hydra_runner(config_path="conf", config_name="rad-tts_dec")
def main(cfg):
    trainer = pl.Trainer(**cfg.trainer)
    exp_manager(trainer, cfg.get('exp_manager', None))
    model = RadTTSModel(cfg=cfg.model, trainer=trainer)
    if cfg.model.load_from_checkpoint:
        model.maybe_init_from_pretrained_checkpoint(cfg=cfg.model)
        prepare_model_weights(model, cfg.model.trainerConfig.unfreeze_modules)
    lr_logger = pl.callbacks.LearningRateMonitor()
    epoch_time_logger = LogEpochTimeCallback()
    trainer.callbacks.extend([lr_logger, epoch_time_logger])
    trainer.fit(model)


if __name__ == '__main__':
    main()
