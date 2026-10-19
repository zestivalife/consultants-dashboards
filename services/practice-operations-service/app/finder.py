"""Deterministic, non-clinical public consultant finder policy."""
from pydantic import BaseModel,Field

SUPPORT_TAXONOMY={
 "NUTRITION":{"label":"Nutrition & Healthy Eating","professions":["DIETITIAN","NUTRITIONIST"]},
 "EMOTIONAL_WELLBEING":{"label":"Stress & Emotional Wellbeing","professions":["PSYCHOLOGIST","MENTAL_WELLNESS_THERAPIST"]},
 "HABIT_CHANGE":{"label":"Behaviour & Habits","professions":["HEALTH_COACH","BEHAVIOURAL_THERAPIST"]},
 "MOVEMENT_REHAB":{"label":"Movement / Pain / Rehabilitation","professions":["PHYSIOTHERAPIST"]},
 "DIABETES_SELF_MANAGEMENT":{"label":"Diabetes Education","professions":["DIABETES_EDUCATOR"]},
 "DAILY_LIVING":{"label":"Daily Living / Occupational Support","professions":["OCCUPATIONAL_THERAPIST"]},
 "GENERAL_WELLNESS":{"label":"General Wellness","professions":["WELLNESS_CONSULTANT"]},
 "HEALTH_COACHING":{"label":"Health Coaching","professions":["HEALTH_COACH"]},
 "MENTAL_WELLNESS":{"label":"Mental Wellness Support","professions":["MENTAL_WELLNESS_THERAPIST","PSYCHOLOGIST"]},
}
FINDER_EVENTS={"FINDER_STARTED","FINDER_STEP_COMPLETED","FINDER_COMPLETED","FINDER_RESULT_VIEW","FINDER_PROFILE_CLICK","FINDER_SAVE","FINDER_COMPARE","FINDER_ENROL_CLICK","FINDER_BOOK_CLICK"}

class FinderRequest(BaseModel):
 support_area:str
 mode:str=Field(pattern="^(ONLINE|IN_PERSON|EITHER)$")
 location:str|None=Field(default=None,max_length=120)
 languages:list[str]=Field(default_factory=list,max_length=5)
 availability:str=Field(default="NO_PREFERENCE",pattern="^(EARLIEST|TODAY|WITHIN_3_DAYS|WITHIN_7_DAYS|NO_PREFERENCE)$")
 budget_min:int|None=Field(default=None,ge=0)
 budget_max:int|None=Field(default=None,ge=0)
 currency:str|None=Field(default=None,pattern="^[A-Z]{3}$")
 experience_min:int|None=Field(default=None,ge=0,le=80)

class FinderEvent(BaseModel):
 event_type:str
 step:str|None=Field(default=None,max_length=40)
 support_area:str|None=Field(default=None,max_length=80)
 profile_id:str|None=None

def explain_and_score(projection,request,available):
 reasons=["Relevant professional category"]
 score=100
 modes=projection.get("consultation_modes") or []
 if request.mode=="ONLINE" and ("ONLINE" in modes or "BOTH" in modes):reasons.append("Available online");score+=25
 if request.mode=="IN_PERSON" and ("IN_PERSON" in modes or "BOTH" in modes):reasons.append("Offers in-person consultations");score+=25
 if request.location and any(request.location.lower()==str(x.get("name","")).lower() for x in projection.get("public_locations") or []):reasons.append(f"Available in {request.location}");score+=15
 public_languages={str(x).lower() for x in projection.get("languages") or []}
 matched=[x for x in request.languages if x.lower() in public_languages]
 if matched:reasons.append(f"Speaks {matched[0]}");score+=15
 if available and request.availability!="NO_PREFERENCE":reasons.append("Public availability matches your timeframe");score+=12
 fee=projection.get("public_fee_from");currency=projection.get("public_fee_currency")
 if request.currency and currency==request.currency and fee is not None and (request.budget_min is None or fee>=request.budget_min) and (request.budget_max is None or fee<=request.budget_max):reasons.append("Within your selected fee range");score+=10
 if request.experience_min is not None and int(projection.get("experience_years") or 0)>=request.experience_min:reasons.append("Matches your experience preference");score+=8
 return score,reasons
