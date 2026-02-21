import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { Navigate, useNavigate } from 'react-router-dom';
import { authApi } from '@/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { useAuth } from '@/contexts/AuthContext';

export default function PasswordChangePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { success, error: showError } = useToast();
  
  const [formData, setFormData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const changePasswordMutation = useMutation({
    mutationFn: (data: { old_password: string; new_password: string }) =>
      authApi.changePassword(data.old_password, data.new_password),
    onSuccess: () => {
      success(t('auth.passwordChanged'));
      navigate('/ho-so');
    },
    onError: (err: Error & { response?: { data?: Record<string, string[]> } }) => {
      if (err.response?.data) {
        const apiErrors: Record<string, string> = {};
        Object.entries(err.response.data).forEach(([key, value]) => {
          apiErrors[key] = Array.isArray(value) ? value[0] : String(value);
        });
        setErrors(apiErrors);
      } else {
        showError(t('common.error'));
      }
    },
  });

  // Redirect if not authenticated - must be after all hooks
  if (!isAuthenticated) {
    return <Navigate to="/dang-nhap" replace />;
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error when user types
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate
    const newErrors: Record<string, string> = {};
    
    if (!formData.old_password) {
      newErrors.old_password = t('auth.oldPasswordRequired');
    }
    if (!formData.new_password) {
      newErrors.new_password = t('auth.newPasswordRequired');
    } else if (formData.new_password.length < 8) {
      newErrors.new_password = t('auth.passwordTooShort');
    }
    if (formData.new_password !== formData.confirm_password) {
      newErrors.confirm_password = t('auth.passwordMismatch');
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    changePasswordMutation.mutate({
      old_password: formData.old_password,
      new_password: formData.new_password,
    });
  };

  return (
    <div className="max-w-md mx-auto">
      <Card className="border-vintage-tan/30 shadow-lg">
        <CardHeader className="bg-vintage-cream border-b border-vintage-tan/20">
          <CardTitle className="text-2xl font-serif text-vintage-dark">
            {t('auth.changePassword')}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label={t('auth.currentPassword')}
              type="password"
              name="old_password"
              value={formData.old_password}
              onChange={handleChange}
              error={errors.old_password}
              required
            />
            
            <Input
              label={t('auth.newPassword')}
              type="password"
              name="new_password"
              value={formData.new_password}
              onChange={handleChange}
              error={errors.new_password}
              required
            />
            
            <Input
              label={t('auth.confirmNewPassword')}
              type="password"
              name="confirm_password"
              value={formData.confirm_password}
              onChange={handleChange}
              error={errors.confirm_password}
              required
            />
            
            <div className="flex gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/ho-so')}
                className="flex-1"
              >
                {t('common.cancel')}
              </Button>
              <Button
                type="submit"
                disabled={changePasswordMutation.isPending}
                className="flex-1 bg-vintage-olive hover:bg-vintage-brown"
              >
                {changePasswordMutation.isPending ? t('common.loading') : t('auth.changePassword')}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
