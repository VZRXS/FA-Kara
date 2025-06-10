import torch
import torchaudio
import math

def align_audio_with_text(audio_file_path, text_tokens):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    try:
        bundle = torchaudio.pipelines.MMS_FA
        waveform, sample_rate = torchaudio.load(audio_file_path)

        waveform = waveform.mean(0, keepdim=True)
        waveform = torchaudio.functional.resample(
            waveform, sample_rate, int(bundle.sample_rate)
        )

        model = bundle.get_model().to(device)
        tokenizer = bundle.get_tokenizer()
        aligner = bundle.get_aligner()

        valid_tokens = [token for token in text_tokens if token]

        with torch.inference_mode():
            emission, _ = model(waveform.to(device))
            tokens = tokenizer(valid_tokens)
            token_spans = aligner(emission[0], tokens)

        results = []
        frame_duration = 1.0 / bundle.sample_rate * 320

        for i, spans in enumerate(token_spans):
            if not spans:
                results.append({
                    'token': valid_tokens[i],
                    'start': '[error]',
                    'end': '[error]'
                })
                continue

            start_time = spans[0].start * frame_duration
            end_time = spans[-1].end * frame_duration

            def format_time(time_sec):
                minutes, remainder = divmod(time_sec, 60)
                seconds, centiseconds = divmod(remainder, 1)
                return f"[{int(minutes):02d}:{int(seconds):02d}:{math.floor(centiseconds * 100):02d}]"

            results.append({
                'token': valid_tokens[i],
                'start': format_time(start_time),
                'end': format_time(end_time)
            })

        return results

    except Exception as e:
        print(f"Error during alignment: {e}")
        return []