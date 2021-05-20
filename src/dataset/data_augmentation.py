import random
import torchaudio.transforms as T
from torchaudio.sox_effects import apply_effects_tensor

from settings import *


pitch_shift_probability = 0.5
pitch_shift_min = -4
pitch_shift_max = 4  # 4 semitones

tempo_shift_probability = 0.5
tempo_shift_min = 0.85
tempo_shift_max = 1.25

gaussian_noise_probability = 0.5
gaussian_noise_strength = 0.001

frequency_mask_probability = 0.5
frequency_mask_height = 10

time_mask_probability = 0.5
time_mask_frame_probability = 0.2
time_mask_frame_percentage = 0.5


def augment_record(record):
    waveform, phonemes = record
    effects = [
        ['remix', '-'],  # merge all channels
    ]
    # pitch shift
    if random.random() < pitch_shift_probability:
        pitch_factor = floor2(random.uniform(
            pitch_shift_min, pitch_shift_max))
        effects.append(['pitch', f'{pitch_factor * 100}'])
    # tempo shift
    if random.random() < tempo_shift_probability:
        tempo_factor = floor2(random.uniform(tempo_shift_min, tempo_shift_max))
        effects.append(['tempo', f'{tempo_factor}'])
        # update phoneme boundaries
        for pn in phonemes:
            pn.start = int(round(pn.start / tempo_factor))
            pn.stop = int(round(pn.stop / tempo_factor))
    # apply to record
    if len(effects) > 2:
        effects.append(['rate', f'{SAMPLE_RATE}'])
        waveform, _ = apply_effects_tensor(
            waveform.reshape(1, -1), SAMPLE_RATE, effects, channels_first=True)
        waveform = waveform[0]
    return waveform, phonemes


def augment_fbank(specgrams):
    # gaussian noise
    if random.random() < gaussian_noise_probability:
        noise = torch.randn(specgrams.shape)
        specgrams += noise * gaussian_noise_strength
    # frequency mask
    if random.random() < frequency_mask_probability:
        torch.random.manual_seed(4)
        masking = T.FrequencyMasking(freq_mask_param=frequency_mask_height)
        specgrams = masking(specgrams)
    # time mask
    if random.random() < time_mask_probability:
        for i in range(0, specgrams.size(1) - FRAME_RESOLUTION, FRAME_RESOLUTION):
            if random.random() < time_mask_frame_probability:
                frame = specgrams.narrow(1, i, FRAME_RESOLUTION)
                torch.random.manual_seed(4)
                masking = T.TimeMasking(time_mask_param=int(
                    FRAME_RESOLUTION * time_mask_frame_percentage))
                specgrams[:, i:i+FRAME_RESOLUTION] = masking(frame)
    return specgrams


def floor2(x):  # floor to 2 decimals
    return x // 0.01 / 100
