# Automatic LBW Review Assistant

Upload a cricket video and the app automatically estimates whether the
delivery is **LBW Out**, **Not Out**, or **Uncertain**. The main workflow no
longer asks the user to enter the LBW conditions manually.

This is a portfolio-grade computer-vision MVP and a decision-support tool, not
an official umpiring system. A single broadcast angle may not show the
bowling front foot, bat-pad order, or true pitch geometry. When evidence is
missing, the application returns **Uncertain** instead of inventing a verdict.

## Quick start

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
streamlit run app.py
```

Then open the local Streamlit URL and upload an MP4, MOV, AVI, or MKV clip.
The app automatically selects an evidence frame, draws the tracked ball path,
and produces a JSON report.

## Automatic pipeline

1. Reads video metadata and tracks likely cricket-ball candidates.
2. Estimates the bounce from the descending-to-rising trajectory transition.
3. Detects a visible wicket corridor from vertical stump-line evidence.
4. Estimates the impact region and projected wicket hit.
5. Detects a strong post-bounce direction reversal as a bat-first cue.
6. Applies conservative LBW rules and reports the evidence for each condition.

The lightweight baseline uses OpenCV colour segmentation, Hough circles,
trajectory geometry, and explainable rules. It does not require the user to
select no-ball, pitch, impact, bat-first, shot, or wicket-hit values.

## Important automatic limitations

- No-ball status is **Unknown** unless a future pose/crease model can verify the
  bowler's front foot. The UI also shows a conditional result if every other
  condition would pass assuming a legal delivery.
- A side-on view cannot reliably recover true lateral pitch coordinates. The
  baseline therefore uses the post-bounce path and reports uncertainty when it
  cannot establish eligibility.
- The location heuristic assumes image-left is leg side and image-right is off
  side. Reversed camera views need camera calibration.
- Treat **Uncertain** as a request for a better angle or more evidence.

## Sample videos

The `sample_videos/` directory contains short synthetic clips for testing:

- `sample_lbw_like.mp4`
- `sample_not_out_bat_first.mp4`
- `sample_not_out_outside_leg.mp4`

They are demonstrations, not real match footage or a training dataset.

## Project layout

```text
lbw-review-assistant/
├── app.py
├── requirements.txt
├── requirements-optional.txt
├── Dockerfile
├── pyproject.toml
├── sample_videos/
├── src/lbw_review/
│   ├── detector.py
│   ├── geometry.py
│   ├── models.py
│   ├── render.py
│   ├── rules.py
│   └── video.py
└── tests/
```

## Production upgrade path

For reliable real-match analysis, replace the heuristic detector with a
labelled cricket dataset and a trained multi-object/video model for ball, bat,
pad, stumps, crease, batter, and bowler-foot keypoints. Add camera calibration,
multi-view or high-frame-rate trajectory reconstruction, and evaluate with
precision/recall plus calibrated uncertainty. `requirements-optional.txt`
contains the optional Ultralytics/PyTorch stack for integrating such a model.

## License

MIT. See `LICENSE`.
