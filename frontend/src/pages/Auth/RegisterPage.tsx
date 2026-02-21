import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import Spinner from '@/components/ui/Spinner';

export default function RegisterPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { register } = useAuth();
  
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
    target_language: '',
    level: '',
    skill_focus: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
    // Clear field error
    if (errors[e.target.name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[e.target.name];
        return newErrors;
      });
    }
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.username) {
      newErrors.username = t('auth.register.errors.usernameRequired');
    }
    if (!formData.email) {
      newErrors.email = t('auth.register.errors.emailRequired');
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = t('auth.register.errors.emailInvalid');
    }
    if (!formData.password) {
      newErrors.password = t('auth.register.errors.passwordRequired');
    } else if (formData.password.length < 8) {
      newErrors.password = t('auth.register.errors.passwordLength');
    }
    if (formData.password !== formData.password2) {
      newErrors.password2 = t('auth.register.errors.passwordMismatch');
    }
    if (!agreedToTerms) {
      newErrors.terms = t('auth.register.errors.termsRequired', 'Bạn phải đồng ý với điều khoản dịch vụ');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) return;

    setIsSubmitting(true);

    try {
      await register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        password2: formData.password2,
        first_name: formData.first_name,
        last_name: formData.last_name,
        target_language: formData.target_language || undefined,
        level: formData.level || undefined,
        skill_focus: formData.skill_focus || undefined,
      });
      navigate('/');
    } catch (err: unknown) {
      const error = err as { response?: { data?: Record<string, string[]> } };
      if (error.response?.data) {
        const apiErrors: Record<string, string> = {};
        Object.entries(error.response.data).forEach(([key, value]) => {
          apiErrors[key] = Array.isArray(value) ? value[0] : value as string;
        });
        setErrors(apiErrors);
      } else {
        setErrors({ general: t('auth.register.error') });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto py-12">
      <Card>
        <CardHeader>
          <CardTitle className="text-center text-2xl">
            {t('auth.register.title')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {errors.general && (
              <div className="p-3 bg-destructive/10 text-destructive rounded-lg text-sm">
                {errors.general}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <Input
                label={t('auth.register.firstName')}
                name="first_name"
                type="text"
                value={formData.first_name}
                onChange={handleChange}
                error={errors.first_name}
              />
              <Input
                label={t('auth.register.lastName')}
                name="last_name"
                type="text"
                value={formData.last_name}
                onChange={handleChange}
                error={errors.last_name}
              />
            </div>

            <Input
              label={t('auth.register.username')}
              name="username"
              type="text"
              value={formData.username}
              onChange={handleChange}
              required
              error={errors.username}
              autoComplete="username"
            />

            <Input
              label={t('auth.register.email')}
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              required
              error={errors.email}
              autoComplete="email"
            />

            <Input
              label={t('auth.register.password')}
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              required
              error={errors.password}
              autoComplete="new-password"
            />

            <Input
              label={t('auth.register.confirmPassword')}
              name="password2"
              type="password"
              value={formData.password2}
              onChange={handleChange}
              required
              error={errors.password2}
              autoComplete="new-password"
            />

            <Select
              label={t('auth.register.targetLanguage')}
              name="target_language"
              value={formData.target_language}
              onChange={handleChange}
              options={[
                { value: 'en', label: `🇬🇧 ${t('languages.en')}` },
                { value: 'de', label: `🇩🇪 ${t('languages.de')}` },
              ]}
              placeholder={t('auth.register.selectLanguage')}
            />

            <Select
              label={t('auth.register.level')}
              name="level"
              value={formData.level}
              onChange={handleChange}
              options={[
                { value: 'A1', label: t('levels.A1') },
                { value: 'A2', label: t('levels.A2') },
                { value: 'B1', label: t('levels.B1') },
                { value: 'B2', label: t('levels.B2') },
                { value: 'C1', label: t('levels.C1') },
                { value: 'C2', label: t('levels.C2') },
              ]}
              placeholder={t('auth.register.selectLevel')}
            />

            <Select
              label={t('auth.register.skillFocus')}
              name="skill_focus"
              value={formData.skill_focus}
              onChange={handleChange}
              options={[
                { value: 'speaking', label: t('skills.speaking') },
                { value: 'listening', label: t('skills.listening') },
                { value: 'reading', label: t('skills.reading') },
                { value: 'writing', label: t('skills.writing') },
                { value: 'grammar', label: t('skills.grammar') },
                { value: 'vocabulary', label: t('skills.vocabulary') },
                { value: 'all', label: t('skills.all') },
              ]}
              placeholder={t('auth.register.selectSkill')}
            />

            {/* Terms checkbox */}
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id="terms"
                checked={agreedToTerms}
                onChange={(e) => setAgreedToTerms(e.target.checked)}
                className="mt-1 h-4 w-4 text-vintage-olive focus:ring-vintage-brown border-vintage-tan rounded"
              />
              <label htmlFor="terms" className="text-sm text-vintage-dark/80">
                {t('auth.register.agreeToTerms', 'Tôi đồng ý với')}{' '}
                <Link to="/dieu-khoan" className="text-vintage-brown hover:text-vintage-olive font-medium">
                  {t('auth.register.terms', 'Điều khoản dịch vụ')}
                </Link>{' '}
                {t('common.and', 'và')}{' '}
                <Link to="/bao-mat" className="text-vintage-brown hover:text-vintage-olive font-medium">
                  {t('auth.register.privacy', 'Chính sách bảo mật')}
                </Link>
              </label>
            </div>
            {errors.terms && (
              <p className="text-sm text-destructive">{errors.terms}</p>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <Spinner size="sm" className="mr-2" />
              ) : null}
              {t('auth.register.submit')}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm">
            <p className="text-muted-foreground">
              {t('auth.register.hasAccount')}{' '}
              <Link to="/dang-nhap" className="text-primary hover:underline">
                {t('auth.register.login')}
              </Link>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
