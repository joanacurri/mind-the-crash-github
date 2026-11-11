# Dashboard choices and assumptions

These are our choices, not the model's: they should be stated if anyone asks "where does this come from?".

## From the call handler's answers to the 40 variables (`js/call.js`)

| Answer | How it becomes a variable | Why / limitation |
|---|---|---|
| "Don't know" to a question | stays at the **training median** (`X_tr.median()`) | for 0/1 variables the median is almost always the most common value |
| "Don't know" for age | average of the estimates as child / adult / older person, weighted 9% / 80% / 11% | the median is 35, the value used to fill missing ages: the model reads it as "probably slight" |
| Age bands | child = 11, adult = 34, older person = 74 years | medians of the real casualty ages (0–15, 16–64, 65+) |
| Number of vehicles | sum of the counters, minimum 1, maximum 4 | the model saw counts capped at 4 |
| Drivers injured | all casualties on motorcycles/bicycles + one casualty per car + one per van | **assumption**: the first casualty in each vehicle is the driver |
| Passengers injured | casualties in vehicles minus the drivers | follows from the row above |
| Pedestrian crossing | all injured pedestrians were crossing | simplification |
| "Vans, lorries or buses" | a single counter; "In a van" casualties go to `casualty_type_Van` | the model does not separate lorries and buses among the selected variables |
| Head-on | front impact on 2 vehicles (1 if there is only one) | **assumption** |
| Rear-end | 1 front impact + 1 back impact | **assumption** |
| Side | 1 front impact + 1 side impact | **assumption** |
| All going ahead / One was turning / One was stopped or slowing | all going ahead / one turning / one stopped or slowing | |
| Left the road / Hit a tree | left the carriageway nearside / plus tree | the side is arbitrary |
| Type of road | dual carriageway = neither single carriageway nor main/local; main road; local road | **assumption** on the mapping |
| Junction | no = all not at junction; traffic lights; give way or uncontrolled | |
| Overturned | 1 vehicle overturned, the others "no skidding" | |
| Main carriageway | all vehicles on the main carriageway | not asked |
| Sex of driver | training median | not asked |

## Automatic data

- **Location**: drawn at random from 2,000 real collisions in the test set (seed 42); it provides latitude, longitude, urban/rural, `collision_injury_based` and the suggested speed limit. It simulates the phone's location ping.
- **Time**: from the computer clock; it gives the week of the year (`woy`) and "afternoon" (12–18).

## Verdict and action

- The verdict only appears after at least one vehicle and one casualty: with no answers the estimate falls right on the threshold.
- Threshold 0.221 (from the model). Slide 22 says 0.222.
- "What moved the estimate": how much the probability changes if that answer becomes "Don't know".
- "What to do now": **does not come from the model**. Serious → Category 2 ambulance; Slight → Category 3; rural + Serious → consider the helicopter.
  If the caller reports someone not breathing, unconscious or bleeding heavily → Category 1, whatever the estimate. The categories are those of NHS England (Ambulance Response Programme); the real category is assigned by clinical triage.

## Analysis pages

- **How the estimate works**: test-set scores (154,124 collisions) grouped at 0.001, so exact for any 3-decimal threshold.
- **What the model listens to**: SHAP values on 30,000 test-set collisions (seed 42), summed by question; the 16 answers are defined in `scripts/prep_importance.py`; for the age bands, ages of exactly 35 are excluded.
- **Where collisions turn serious**: hexagons of radius 0.14° (longitude corrected for latitude 54.5°); grey below 30 collisions (or 15 serious in the "missed" view); 5 colour classes with the same number of hexagons; the name shows the 2 districts with the most collisions and the prevailing police force.
