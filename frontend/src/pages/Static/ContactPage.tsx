import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { SEO } from '@/components/common';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { useToast } from '@/components/ui/Toast';
import { Mail, MapPin, Send, MessageSquare } from 'lucide-react';
import api from '@/api/client';

export default function ContactPage() {
  const { t } = useTranslation();
  const { error: showError } = useToast();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFieldErrors({});
    
    try {
      await api.post('/contact/', formData);
      setSubmitted(true);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { errors?: Record<string, string> } } };
      if (error.response?.data?.errors) {
        setFieldErrors(error.response.data.errors);
      } else {
        showError(t('common.error', 'Đã xảy ra lỗi. Vui lòng thử lại sau.'));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      <SEO 
        title={t('contact.seo.title')}
        description={t('contact.seo.description')}
        keywords={['liên hệ UnstressVN', 'hỗ trợ học ngoại ngữ', 'chăm sóc khách hàng', 'góp ý']}
        type="website"
      />

      <div className="container-responsive section-spacing">
        {/* Header */}
        <section className="text-center mb-10 md:mb-12">
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-serif font-bold text-vintage-dark mb-4">
            {t('contact.title')}
          </h1>
          <p className="max-w-xl mx-auto text-base md:text-lg text-vintage-dark/70 font-serif italic">
            {t('contact.subtitle')}
          </p>
          <div className="mt-6 w-24 h-1 bg-vintage-brown mx-auto rounded-full opacity-50"></div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 md:gap-10">
          {/* Contact Info */}
          <div className="space-y-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-vintage-olive/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Mail className="h-5 w-5 text-vintage-olive" />
                  </div>
                  <div>
                    <h3 className="font-serif font-bold text-vintage-dark mb-1">
                      {t('contact.email.title')}
                    </h3>
                    <p className="text-vintage-dark/70 text-sm mb-2">
                      {t('contact.email.description')}
                    </p>
                    <a href="mailto:unstressvn@gmail.com" className="text-vintage-olive hover:text-vintage-brown font-medium">
                      unstressvn@gmail.com
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-vintage-blue/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <MessageSquare className="h-5 w-5 text-vintage-blue" />
                  </div>
                  <div>
                    <h3 className="font-serif font-bold text-vintage-dark mb-1">
                      {t('contact.chat.title')}
                    </h3>
                    <p className="text-vintage-dark/70 text-sm mb-2">
                      {t('contact.chat.description')}
                    </p>
                    <a href="/cong-dong" className="text-vintage-blue hover:text-vintage-brown font-medium">
                      {t('contact.chat.link')} →
                    </a>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-vintage-brown/10 rounded-lg flex items-center justify-center flex-shrink-0">
                    <MapPin className="h-5 w-5 text-vintage-brown" />
                  </div>
                  <div>
                    <h3 className="font-serif font-bold text-vintage-dark mb-1">
                      {t('contact.location.title')}
                    </h3>
                    <p className="text-vintage-dark/70 text-sm">
                      {t('contact.location.address', 'Hanoi, Vietnam')}<br />
                      {t('contact.location.remote')}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Contact Form */}
          <div className="lg:col-span-2">
            <Card>
              <CardContent className="p-6 md:p-8">
                {submitted ? (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 bg-vintage-olive/15 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Send className="h-8 w-8 text-green-600" />
                    </div>
                    <h3 className="text-xl font-serif font-bold text-vintage-dark mb-2">
                      {t('contact.success.title')}
                    </h3>
                    <p className="text-vintage-dark/70">
                      {t('contact.success.description')}
                    </p>
                    <Button 
                      onClick={() => {
                        setSubmitted(false);
                        setFormData({ name: '', email: '', subject: '', message: '' });
                      }}
                      className="mt-6"
                    >
                      {t('contact.success.sendAnother')}
                    </Button>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
                      <div>
                        <label className="label">{t('contact.form.name')}</label>
                        <Input
                          required
                          value={formData.name}
                          onChange={(e) => { setFormData({ ...formData, name: e.target.value }); setFieldErrors((prev) => ({ ...prev, name: '' })); }}
                          placeholder={t('contact.form.namePlaceholder')}
                        />
                        {fieldErrors.name && <p className="text-sm text-vintage-brown mt-1">{fieldErrors.name}</p>}
                      </div>
                      <div>
                        <label className="label">{t('contact.form.email')}</label>
                        <Input
                          type="email"
                          required
                          value={formData.email}
                          onChange={(e) => { setFormData({ ...formData, email: e.target.value }); setFieldErrors((prev) => ({ ...prev, email: '' })); }}
                          placeholder={t('contact.form.emailPlaceholder')}
                        />
                        {fieldErrors.email && <p className="text-sm text-vintage-brown mt-1">{fieldErrors.email}</p>}
                      </div>
                    </div>

                    <div>
                      <label className="label">{t('contact.form.subject')}</label>
                      <Input
                        required
                        value={formData.subject}
                        onChange={(e) => { setFormData({ ...formData, subject: e.target.value }); setFieldErrors((prev) => ({ ...prev, subject: '' })); }}
                        placeholder={t('contact.form.subjectPlaceholder')}
                      />
                      {fieldErrors.subject && <p className="text-sm text-vintage-brown mt-1">{fieldErrors.subject}</p>}
                    </div>

                    <div>
                      <label className="label">{t('contact.form.message')}</label>
                      <textarea
                        required
                        rows={6}
                        value={formData.message}
                        onChange={(e) => { setFormData({ ...formData, message: e.target.value }); setFieldErrors((prev) => ({ ...prev, message: '' })); }}
                        placeholder={t('contact.form.messagePlaceholder')}
                        className="input resize-none"
                      />
                      {fieldErrors.message && <p className="text-sm text-vintage-brown mt-1">{fieldErrors.message}</p>}
                    </div>

                    <Button 
                      type="submit" 
                      disabled={isSubmitting}
                      className="w-full md:w-auto touch-target"
                    >
                      {isSubmitting ? (
                        <span className="flex items-center gap-2">
                          <span className="spinner h-4 w-4"></span>
                          {t('common.sending')}
                        </span>
                      ) : (
                        <span className="flex items-center gap-2">
                          <Send className="h-4 w-4" />
                          {t('contact.form.submit')}
                        </span>
                      )}
                    </Button>
                  </form>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}
