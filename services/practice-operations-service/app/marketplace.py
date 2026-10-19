"""P31 marketplace lifecycle and public-projection policy."""
import hashlib,re
from datetime import date,datetime,timezone
from pydantic import BaseModel,Field,field_validator

PUBLIC_FIELDS={"profile_photo_url","display_name","professional_title","profession_code","specialisations","experience_years","bio","languages","consultation_modes","areas_of_focus","public_locations","services","programmes","session_duration","public_fee_from","public_fee_currency","accepting_new_clients"}
PRIVATE_FIELDS={"aadhaar","pan","identity_proof","private_address","private_email","private_phone","bank_details","verification_notes","admin_notes","tenant_secret","credential_document_url"}
PROFILE_TRANSITIONS={
 "DRAFT":{"SUBMITTED_FOR_REVIEW"},"SUBMITTED_FOR_REVIEW":{"DRAFT","UNDER_REVIEW"},"UNDER_REVIEW":{"CHANGES_REQUIRED","APPROVED","REJECTED"},
 "CHANGES_REQUIRED":{"DRAFT","SUBMITTED_FOR_REVIEW"},"APPROVED":{"PUBLISHED","UNPUBLISHED"},"PUBLISHED":{"UNPUBLISHED","SUSPENDED"},
 "UNPUBLISHED":{"PUBLISHED","SUSPENDED"},"REJECTED":{"DRAFT"},"SUSPENDED":{"UNPUBLISHED"}}
ADMIN_ACTIONS={"START_REVIEW":"UNDER_REVIEW","REQUEST_CHANGES":"CHANGES_REQUIRED","APPROVE_PROFILE":"APPROVED","REJECT_PROFILE":"REJECTED","PUBLISH_PROFILE":"PUBLISHED","UNPUBLISH_PROFILE":"UNPUBLISHED","SUSPEND_PROFILE":"SUSPENDED","RESTORE_PROFILE":"UNPUBLISHED"}
REASON_REQUIRED={"REQUEST_CHANGES","REJECT_PROFILE","UNPUBLISH_PROFILE","SUSPEND_PROFILE","REJECT_QUALIFICATION","REJECT_REVIEW","HIDE_REVIEW"}

class PublicLocation(BaseModel):
    id:str;name:str=Field(min_length=2,max_length=240);mode:str=Field(pattern="^(ONLINE|IN_PERSON|PHONE|OTHER)$")

class PublicService(BaseModel):
    id:str;name:str=Field(min_length=2,max_length=240);description:str|None=Field(default=None,max_length=1000)
    duration:int=Field(ge=5,le=480);mode:str=Field(pattern="^(ONLINE|IN_PERSON|PHONE|OTHER)$");location_id:str|None=None
    fee:int|None=Field(default=None,ge=0);currency:str|None=Field(default=None,pattern="^[A-Z]{3}$");enrolment_mode:str=Field(pattern="^(REQUEST_ENROLMENT|DIRECT_BOOKING)$");active:bool=True

class PublicProgramme(BaseModel):
    id:str;name:str=Field(min_length=2,max_length=240);description:str|None=Field(default=None,max_length=2000);fee:int|None=Field(default=None,ge=0);currency:str|None=Field(default=None,pattern="^[A-Z]{3}$");active:bool=True

class ProfileSave(BaseModel):
    display_name:str=Field(min_length=2,max_length=160);professional_title:str=Field(min_length=2,max_length=180);profession_code:str=Field(min_length=2,max_length=80)
    profile_photo_url:str|None=None;specialisations:list[str]=Field(default_factory=list,max_length=20);experience_years:int=Field(ge=0,le=80)
    bio:str=Field(min_length=20,max_length=4000);languages:list[str]=Field(default_factory=list,max_length=20);consultation_modes:list[str]=Field(default_factory=list,max_length=4)
    areas_of_focus:list[str]=Field(default_factory=list,max_length=30);public_locations:list[PublicLocation]=Field(default_factory=list,max_length=20);services:list[PublicService]=Field(default_factory=list,max_length=30)
    programmes:list[PublicProgramme]=Field(default_factory=list,max_length=30);session_duration:int|None=Field(default=None,ge=10,le=480);public_fee_from:int|None=Field(default=None,ge=0);public_fee_currency:str|None=Field(default=None,pattern="^[A-Z]{3}$")
    accepting_new_clients:bool=False
    @field_validator("profile_photo_url")
    @classmethod
    def safe_photo(cls,value):
        if value and not (value.startswith("https://") or value.startswith("/")):raise ValueError("Public photo must use an approved HTTPS or same-origin derivative")
        if value and any(marker in value.lower() for marker in ("object_key","presigned","signature=","x-amz-")):raise ValueError("Private object references cannot be used as public photos")
        return value

class QualificationCreate(BaseModel):
    qualification_type:str=Field(min_length=2,max_length=80);title:str=Field(min_length=2,max_length=240);institution:str=Field(min_length=2,max_length=240)
    award_year:int=Field(ge=1900,le=date.today().year);country:str|None=Field(default=None,max_length=100);registration_number:str|None=Field(default=None,max_length=160)
    issuing_body:str|None=Field(default=None,max_length=240);expiry_date:date|None=None;credential_document_id:str|None=None

class AdminDecision(BaseModel):action:str;reason:str|None=Field(default=None,max_length=1000)
class QualificationDecision(BaseModel):action:str;reason:str|None=Field(default=None,max_length=1000)
class EnrolmentCreate(BaseModel):
    full_name:str=Field(min_length=2,max_length=240);email:str|None=Field(default=None,max_length=320);phone:str|None=Field(default=None,max_length=60)
    service_id:str|None=None;programme_id:str|None=None;consultation_mode:str|None=Field(default=None,max_length=40);location_id:str|None=None
    preferred_at:datetime|None=None;message:str|None=Field(default=None,max_length=1000);consent_acknowledged:bool
    source:str=Field(default="PUBLIC_CONSULTANT_DIRECTORY",pattern="^(PUBLIC_CONSULTANT_DIRECTORY|HOMEPAGE_FEATURED_CONSULTANT|HOMEPAGE_PROFESSION_DISCOVERY|HOMEPAGE_SEARCH)$")
class ReviewCreate(BaseModel):
    overall_rating:int=Field(ge=1,le=5);review_text:str|None=Field(default=None,max_length=2000);communication_rating:int|None=Field(default=None,ge=1,le=5)
    professionalism_rating:int|None=Field(default=None,ge=1,le=5);support_experience_rating:int|None=Field(default=None,ge=1,le=5)
class EnrolmentAction(BaseModel):action:str;reason:str|None=Field(default=None,max_length=500)
class ReviewReport(BaseModel):reason:str=Field(min_length=3,max_length=1000)
class HomepageFeatureDecision(BaseModel):
    featured_on_homepage:bool
    featured_rank:int|None=Field(default=None,ge=1,le=1000)
    featured_from:datetime|None=None
    featured_until:datetime|None=None
    @field_validator("featured_until")
    @classmethod
    def valid_window(cls,value,info):
        start=info.data.get("featured_from")
        if value and start and value<=start:raise ValueError("Feature window must end after it starts")
        return value
class MarketplaceEventCreate(BaseModel):
    event_type:str=Field(pattern="^(HOMEPAGE_CONSULTANT_IMPRESSION|HOMEPAGE_CONSULTANT_VIEW_CLICK|HOMEPAGE_ENROL_CLICK|HOMEPAGE_DIRECTORY_CLICK|HOMEPAGE_PROFESSION_CLICK)$")
    profile_id:str|None=None
    profession_code:str|None=Field(default=None,max_length=80)

def slug_base(value):return re.sub(r"[^a-z0-9]+","-",value.lower()).strip("-") or "consultant"
def public_projection(payload):return {key:payload.get(key) for key in PUBLIC_FIELDS if key in payload}
def completeness(payload,verified_qualifications=0):
    checks={"Photo":payload.get("profile_photo_url"),"Profession":payload.get("profession_code"),"Title":payload.get("professional_title"),"Bio":payload.get("bio"),"Experience":payload.get("experience_years") is not None,"Specialisation":payload.get("specialisations"),"Verified qualification":verified_qualifications>0,"Consultation mode":payload.get("consultation_modes"),"Service":payload.get("services"),"Location or online":payload.get("public_locations") or "ONLINE" in payload.get("consultation_modes",[])}
    missing=[label for label,ok in checks.items() if not ok];return round((len(checks)-len(missing))*100/len(checks)),missing
def assert_transition(current,target):
    if target not in PROFILE_TRANSITIONS.get(current,set()):raise ValueError(f"Transition {current} to {target} is not allowed")
def can_publish(profile):return profile["status"]=="APPROVED" and profile["approval_valid"] and profile["approved_version"]==profile["working_version"]
def publicly_visible(profile):return profile["status"]=="PUBLISHED" and profile["public_visibility"] and profile["approval_valid"] and not profile.get("suspended_at")
def dedupe_key(profile_id,email,phone,service_id):return hashlib.sha256(f"{profile_id}|{(email or '').strip().lower()}|{(phone or '').strip()}|{service_id or ''}".encode()).hexdigest()
def privacy_safe_name(name):
    parts=(name or "Verified Client").split();return f"{parts[0]} {parts[-1][0]}." if len(parts)>1 else f"{parts[0][0]}." if parts else "Verified Client"
def public_rating(reviews):
    included=[item["overall_rating"] for item in reviews if item.get("verified_engagement") is True and item.get("status")=="PUBLISHED"]
    return {"review_count":len(included),"average_rating":round(sum(included)/len(included),2) if included else None,"label":f"{round(sum(included)/len(included),2)}" if included else "New on Zestiva"}
