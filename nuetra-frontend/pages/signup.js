import { useCallback, useMemo, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, CheckCircle2, Mail, Phone, ShieldCheck } from 'lucide-react';
import RecaptchaCheckbox from '../components/auth/RecaptchaCheckbox';
import { authAPI, persistAuthSession } from '../lib/api';
import { canonicalMobile } from '../lib/mobileIdentity.mjs';

const ROLE_OPTIONS = [
  ['DIETITIAN_NUTRITIONIST', 'Dietitian / Nutritionist'], ['HEALTH_COACH', 'Health Coach'],
  ['WELLNESS_COACH', 'Wellness Coach'], ['PSYCHOLOGIST', 'Psychologist'],
  ['COUNSELLOR_THERAPIST', 'Counsellor / Therapist'], ['PHYSIOTHERAPIST', 'Physiotherapist'],
  ['FITNESS_TRAINER', 'Fitness Trainer'], ['YOGA_MEDITATION_COACH', 'Yoga / Meditation Coach'],
  ['DIABETES_EDUCATOR', 'Diabetes Educator'], ['WOMENS_HEALTH_PRACTITIONER', "Women's Health Practitioner"],
  ['LIFESTYLE_MEDICINE_PRACTITIONER', 'Lifestyle Medicine Practitioner'], ['MENTOR', 'Mentor'],
  ['DOCTOR_PHYSICIAN', 'Doctor / Physician'], ['OTHER_HEALTHCARE_PROFESSIONAL', 'Other Healthcare Professional'],
];

const initialForm = {
  fullName: '', mobileNumber: '', email: '', accountType: 'INDEPENDENT_CONSULTANT', professionalRole: '', yearsExperience: '',
  activeClientRange: '', practiceName: '', qualification: '', certification: '',
  registrationNumber: '', specialization: '', expertise: '', mentorFocus: '', otherRole: '',
};

const qualificationRoles = new Set(['DIETITIAN_NUTRITIONIST', 'PSYCHOLOGIST', 'COUNSELLOR_THERAPIST', 'PHYSIOTHERAPIST', 'DIABETES_EDUCATOR', 'WOMENS_HEALTH_PRACTITIONER', 'LIFESTYLE_MEDICINE_PRACTITIONER', 'DOCTOR_PHYSICIAN', 'OTHER_HEALTHCARE_PROFESSIONAL']);
const certificationRoles = new Set(['HEALTH_COACH', 'WELLNESS_COACH', 'FITNESS_TRAINER', 'YOGA_MEDITATION_COACH']);
const registrationRoles = new Set(['PSYCHOLOGIST', 'PHYSIOTHERAPIST', 'DOCTOR_PHYSICIAN']);
const specializationRoles = new Set(['DIETITIAN_NUTRITIONIST', 'PSYCHOLOGIST', 'COUNSELLOR_THERAPIST', 'PHYSIOTHERAPIST', 'WOMENS_HEALTH_PRACTITIONER', 'LIFESTYLE_MEDICINE_PRACTITIONER', 'DOCTOR_PHYSICIAN']);
const expertiseRoles = new Set(['HEALTH_COACH', 'WELLNESS_COACH', 'FITNESS_TRAINER', 'YOGA_MEDITATION_COACH', 'DIABETES_EDUCATOR', 'MENTOR']);

function fieldError(form, field) {
  if (field === 'fullName' && form.fullName.trim().length < 2) return 'Enter your full name.';
  if (field === 'mobileNumber' && !canonicalMobile(form.mobileNumber)) return 'Enter a valid mobile number with country code.';
  if (field === 'email' && !/^\S+@\S+\.\S+$/.test(form.email.trim())) return 'Enter a valid email address.';
  if (field === 'professionalRole' && !form.professionalRole) return 'Select your professional role.';
  if (field === 'yearsExperience' && (form.yearsExperience === '' || Number(form.yearsExperience) < 0 || Number(form.yearsExperience) > 80)) return 'Enter years of experience from 0 to 80.';
  if (field === 'activeClientRange' && !form.activeClientRange) return 'Select your active-client range.';
  if (field === 'practiceName' && form.accountType === 'PRACTICE_OWNER' && !form.practiceName.trim()) return 'Practice name is required for Practice Owners.';
  if (field === 'qualification' && qualificationRoles.has(form.professionalRole) && !form.qualification.trim()) return 'Enter your primary qualification.';
  if (field === 'certification' && certificationRoles.has(form.professionalRole) && !form.certification.trim()) return 'Enter your relevant certification.';
  if (field === 'registrationNumber' && registrationRoles.has(form.professionalRole) && !form.registrationNumber.trim()) return 'Enter your professional registration number.';
  if (field === 'specialization' && specializationRoles.has(form.professionalRole) && !form.specialization.trim()) return 'Enter your specialization.';
  if (field === 'expertise' && expertiseRoles.has(form.professionalRole) && !form.expertise.trim()) return 'Enter your area of expertise.';
  if (field === 'mentorFocus' && form.professionalRole === 'MENTOR' && !form.mentorFocus.trim()) return 'Enter your mentoring domain.';
  if (field === 'otherRole' && form.professionalRole === 'OTHER_HEALTHCARE_PROFESSIONAL' && !form.otherRole.trim()) return 'Describe your professional role.';
  return '';
}

function InputField({ label, error, children, className = '' }) {
  return <label className={className}><span className="mb-2 block text-sm font-medium text-[#424242]">{label}</span>{children}{error ? <span className="mt-2 block text-xs text-[#b10e1c]">{error}</span> : null}</label>;
}

export default function ExternalConsultantSignupPage() {
  const [form, setForm] = useState(initialForm);
  const [touched, setTouched] = useState({});
  const [captchaToken, setCaptchaToken] = useState('');
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const onCaptcha = useCallback((token) => setCaptchaToken(token), []);
  const fields = useMemo(() => Object.keys(initialForm), []);
  const errors = useMemo(() => Object.fromEntries(fields.map((field) => [field, fieldError(form, field)])), [fields, form]);

  const update = (field) => (event) => setForm((current) => ({ ...current, [field]: event.target.value }));
  const blur = (field) => () => {
    setTouched((current) => ({ ...current, [field]: true }));
    if (field === 'mobileNumber') {
      const canonical = canonicalMobile(form.mobileNumber);
      if (canonical) setForm((current) => ({ ...current, mobileNumber: canonical }));
    }
  };

  async function submit(event) {
    event.preventDefault();
    setTouched(Object.fromEntries(fields.map((field) => [field, true])));
    setError('');
    if (Object.values(errors).some(Boolean)) return;
    if (!captchaToken) { setError('Complete the CAPTCHA before creating your workspace.'); return; }
    setBusy(true);
    try {
      const response = await authAPI.registerExternalConsultant({
        full_name: form.fullName.trim(),
        mobile_number: canonicalMobile(form.mobileNumber),
        email: form.email.trim().toLowerCase(),
        account_type: form.accountType,
        professional_role: form.professionalRole,
        years_experience: Number(form.yearsExperience),
        active_client_range: form.activeClientRange,
        practice_name: form.practiceName.trim() || null,
        qualification: qualificationRoles.has(form.professionalRole) ? form.qualification.trim() : null,
        certification: certificationRoles.has(form.professionalRole) ? form.certification.trim() : null,
        registration_number: registrationRoles.has(form.professionalRole) ? form.registrationNumber.trim() : null,
        specialisation: form.specialization.trim() || null,
        area_of_expertise: form.expertise.trim() || null,
        mentoring_domain: form.mentorFocus.trim() || null,
        profession: form.otherRole.trim() || null,
        recaptcha_token: captchaToken,
      });
      persistAuthSession(response.auth_session, true);
      setResult(response);
    } catch (caught) {
      if (caught.status === 409) setError('An account already exists for this mobile number or email. Sign in to continue.');
      else setError(caught.message || 'Your workspace could not be created. Please review the form and try again.');
    } finally { setBusy(false); }
  }

  if (result) return <main className="fluent-page min-h-screen px-4 py-8 sm:px-6"><section className="fluent-card mx-auto max-w-2xl rounded-[36px] p-6 sm:p-10"><div className="rounded-[28px] border border-[#107c10]/20 bg-[#107c10]/10 p-6"><CheckCircle2 className="h-9 w-9 text-[#107c10]" /><h1 className="mt-4 text-3xl font-semibold text-[#242424]">Workspace created</h1><p className="mt-2 text-sm leading-6 text-[#424242]">Your account and workspace are ready. Complete onboarding to configure your practice.</p><Link href={result.workspace_ready ? '/dashboard/provider' : '/onboarding'} className="fluent-primary-button mt-6 inline-flex items-center gap-2 rounded-[22px] px-5 py-3 text-sm font-medium">Continue<ArrowRight className="h-4 w-4" /></Link></div></section></main>;

  return <main className="fluent-page min-h-screen px-4 py-8 sm:px-6">
    <section className="fluent-card mx-auto max-w-3xl rounded-[36px] p-6 sm:p-10">
      <Link href="/login" className="inline-flex items-center gap-2 text-sm text-[#0f6cbd]"><ArrowLeft className="h-4 w-4" />Back to sign in</Link>
      <p className="mt-8 text-xs uppercase tracking-[0.24em] text-[#0f6cbd]">Fiteatsy Consultant SaaS</p>
      <h1 className="mt-3 text-3xl font-semibold text-[#242424] sm:text-4xl">Create your consultant workspace</h1>
      <p className="mt-3 text-base leading-7 text-[#616161]">Tell us about your practice. You can complete the remaining setup after your workspace is created.</p>
      <form onSubmit={submit} className="mt-8 grid gap-5 sm:grid-cols-2" noValidate>
        <InputField label="Full name" error={touched.fullName && errors.fullName}><input required value={form.fullName} onChange={update('fullName')} onBlur={blur('fullName')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" autoComplete="name" /></InputField>
        <InputField label="Mobile number" error={touched.mobileNumber && errors.mobileNumber}><div className="fluent-input flex items-center gap-3 rounded-[22px] px-4 py-3"><Phone className="h-4 w-4 text-[#616161]" /><input required type="tel" value={form.mobileNumber} onChange={update('mobileNumber')} onBlur={blur('mobileNumber')} placeholder="+91 97620 06688" className="w-full bg-transparent text-sm outline-none" autoComplete="tel" /></div></InputField>
        <InputField label="Email" error={touched.email && errors.email}><div className="fluent-input flex items-center gap-3 rounded-[22px] px-4 py-3"><Mail className="h-4 w-4 text-[#616161]" /><input required type="email" value={form.email} onChange={update('email')} onBlur={blur('email')} className="w-full bg-transparent text-sm outline-none" autoComplete="email" /></div></InputField>
        <InputField label="Professional role" error={touched.professionalRole && errors.professionalRole}><select required value={form.professionalRole} onChange={update('professionalRole')} onBlur={blur('professionalRole')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm"><option value="">Select role</option>{ROLE_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></InputField>
        <InputField label="Account type"><select value={form.accountType} onChange={update('accountType')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm"><option value="INDEPENDENT_CONSULTANT">Independent Consultant</option><option value="PRACTICE_OWNER">Practice Owner</option></select></InputField>
        <InputField label="Years of experience" error={touched.yearsExperience && errors.yearsExperience}><input required type="number" min="0" max="80" value={form.yearsExperience} onChange={update('yearsExperience')} onBlur={blur('yearsExperience')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></InputField>
        <InputField label="Active clients" error={touched.activeClientRange && errors.activeClientRange}><select required value={form.activeClientRange} onChange={update('activeClientRange')} onBlur={blur('activeClientRange')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm"><option value="">Select range</option><option>0</option><option>1-10</option><option>11-25</option><option>26-50</option><option>51-100</option><option>100+</option></select></InputField>
        <InputField label={`Practice / organisation name${form.accountType === 'PRACTICE_OWNER' ? '' : ' (optional)'}`} error={touched.practiceName && errors.practiceName} className="sm:col-span-2"><input required={form.accountType === 'PRACTICE_OWNER'} value={form.practiceName} onChange={update('practiceName')} onBlur={blur('practiceName')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></InputField>
        {qualificationRoles.has(form.professionalRole) ? <InputField label="Primary qualification" error={touched.qualification && errors.qualification}><input value={form.qualification} onChange={update('qualification')} onBlur={blur('qualification')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></InputField> : null}
        {certificationRoles.has(form.professionalRole) ? <InputField label="Relevant certification" error={touched.certification && errors.certification}><input value={form.certification} onChange={update('certification')} onBlur={blur('certification')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></InputField> : null}
        {registrationRoles.has(form.professionalRole) ? <InputField label="Professional registration number" error={touched.registrationNumber && errors.registrationNumber}><input value={form.registrationNumber} onChange={update('registrationNumber')} onBlur={blur('registrationNumber')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></InputField> : null}
        {specializationRoles.has(form.professionalRole) ? <InputField label="Specialisation" error={touched.specialization && errors.specialization}><input value={form.specialization} onChange={update('specialization')} onBlur={blur('specialization')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></InputField> : null}
        {expertiseRoles.has(form.professionalRole) ? <InputField label="Area of expertise" error={touched.expertise && errors.expertise}><input value={form.expertise} onChange={update('expertise')} onBlur={blur('expertise')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></InputField> : null}
        {form.professionalRole === 'MENTOR' ? <InputField label="Mentoring domain" error={touched.mentorFocus && errors.mentorFocus}><input value={form.mentorFocus} onChange={update('mentorFocus')} onBlur={blur('mentorFocus')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></InputField> : null}
        {form.professionalRole === 'OTHER_HEALTHCARE_PROFESSIONAL' ? <InputField label="Profession" error={touched.otherRole && errors.otherRole} className="sm:col-span-2"><input value={form.otherRole} onChange={update('otherRole')} onBlur={blur('otherRole')} className="fluent-input w-full rounded-[22px] px-4 py-3 text-sm" /></InputField> : null}
        <div className="sm:col-span-2 rounded-[22px] border border-black/10 p-4"><div className="mb-3 flex items-center gap-2 text-sm text-[#424242]"><ShieldCheck className="h-4 w-4 text-[#0f6cbd]" />Protected by reCAPTCHA</div><RecaptchaCheckbox onVerify={onCaptcha} /></div>
        <button disabled={busy} className="fluent-primary-button sm:col-span-2 flex w-full items-center justify-center gap-2 rounded-[24px] px-4 py-4 text-sm font-medium disabled:opacity-60">{busy ? 'Creating workspace…' : 'Create Workspace'}<ArrowRight className="h-4 w-4" /></button>
      </form>
      {error ? <div role="alert" className="mt-5 rounded-[20px] border border-[#d13438]/20 bg-[#d13438]/10 px-4 py-3 text-sm text-[#b10e1c]">{error}</div> : null}
      <p className="mt-6 text-center text-sm text-[#616161]">Already have an account? <Link href="/login" className="font-medium text-[#0f6cbd]">Sign in</Link></p>
    </section>
  </main>;
}
