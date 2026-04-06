/**
 * GeminiApiKeyManager — Quản lý API Key Gemini + chọn model cho tính năng dịch phụ đề
 * 
 * - Lưu API key + model vào localStorage
 * - Hiển thị trạng thái key (đã cấu hình / chưa)
 * - Load danh sách model từ server để người dùng chọn
 * - Hướng dẫn chi tiết cách lấy API key miễn phí
 */
import { useState, useCallback, useEffect } from 'react';
import {
  Key,
  Eye,
  EyeOff,
  Trash2,
  Check,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Sparkles,
  Cpu,
  RefreshCw,
} from 'lucide-react';
import { mediaStreamApi, type GeminiModel } from '@/api/mediastream';

const STORAGE_KEY = 'gemini_api_key';
const MODEL_STORAGE_KEY = 'gemini_model';

/** Đọc Gemini API key từ localStorage */
export function getStoredGeminiApiKey(): string {
  try {
    return localStorage.getItem(STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

/** Lưu Gemini API key vào localStorage */
export function setStoredGeminiApiKey(key: string): void {
  try {
    if (key) {
      localStorage.setItem(STORAGE_KEY, key.trim());
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  } catch {
    // localStorage not available
  }
}

/** Xoá Gemini API key khỏi localStorage */
export function removeStoredGeminiApiKey(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // localStorage not available
  }
}

/** Đọc Gemini model từ localStorage */
export function getStoredGeminiModel(): string {
  try {
    return localStorage.getItem(MODEL_STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

/** Lưu Gemini model vào localStorage */
export function setStoredGeminiModel(model: string): void {
  try {
    if (model) {
      localStorage.setItem(MODEL_STORAGE_KEY, model);
    } else {
      localStorage.removeItem(MODEL_STORAGE_KEY);
    }
  } catch {
    // localStorage not available
  }
}

interface GeminiApiKeyManagerProps {
  /** Callback khi key thay đổi (thêm/xoá) */
  onKeyChange?: (key: string) => void;
  /** Callback khi model thay đổi */
  onModelChange?: (model: string) => void;
  /** Hiển thị compact (không có guide) */
  compact?: boolean;
}

export default function GeminiApiKeyManager({ onKeyChange, onModelChange, compact }: GeminiApiKeyManagerProps) {
  const [apiKey, setApiKey] = useState(() => getStoredGeminiApiKey());
  const [inputValue, setInputValue] = useState('');
  const [showInput, setShowInput] = useState(!apiKey);
  const [showKey, setShowKey] = useState(false);
  const [showGuide, setShowGuide] = useState(false);
  const [saved, setSaved] = useState(false);

  // Model selector state
  const [models, setModels] = useState<GeminiModel[]>([]);
  const [defaultModel, setDefaultModel] = useState('');
  const [selectedModel, setSelectedModel] = useState(() => getStoredGeminiModel());
  const [refreshingModels, setRefreshingModels] = useState(false);
  const [refreshError, setRefreshError] = useState('');
  const [refreshSuccess, setRefreshSuccess] = useState('');

  // Fetch models list from server
  useEffect(() => {
    mediaStreamApi.getGeminiModels().then(data => {
      setModels(data.models);
      setDefaultModel(data.default);
      if (!selectedModel) {
        setSelectedModel(data.default);
        onModelChange?.(data.default);
      }
    }).catch(() => { /* silently fail */ });
  }, []);

  const handleRefreshModels = useCallback(async () => {
    const key = apiKey || getStoredGeminiApiKey();
    if (!key) {
      setRefreshError('Cần nhập API Key trước');
      setTimeout(() => setRefreshError(''), 3000);
      return;
    }
    setRefreshingModels(true);
    setRefreshError('');
    setRefreshSuccess('');
    try {
      const data = await mediaStreamApi.refreshGeminiModels(key);
      setModels(data.models);
      setDefaultModel(data.default);
      setRefreshSuccess(`Đã tải ${data.count || data.models.length} models từ Google`);
      setTimeout(() => setRefreshSuccess(''), 4000);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { error?: string } } })?.response?.data?.error || 'Lỗi tải models';
      setRefreshError(msg);
      setTimeout(() => setRefreshError(''), 5000);
    } finally {
      setRefreshingModels(false);
    }
  }, [apiKey]);

  const handleModelChange = useCallback((model: string) => {
    setSelectedModel(model);
    setStoredGeminiModel(model);
    onModelChange?.(model);
  }, [onModelChange]);

  const handleSave = useCallback(() => {
    const trimmed = inputValue.trim();
    if (!trimmed) return;
    setStoredGeminiApiKey(trimmed);
    setApiKey(trimmed);
    setInputValue('');
    setShowInput(false);
    setSaved(true);
    onKeyChange?.(trimmed);
    setTimeout(() => setSaved(false), 2000);
  }, [inputValue, onKeyChange]);

  const handleDelete = useCallback(() => {
    removeStoredGeminiApiKey();
    setApiKey('');
    setShowInput(true);
    onKeyChange?.('');
  }, [onKeyChange]);

  const maskedKey = apiKey
    ? `${apiKey.slice(0, 6)}${'•'.repeat(Math.min(apiKey.length - 10, 20))}${apiKey.slice(-4)}`
    : '';

  return (
    <div className="rounded-lg border border-vintage-tan/30 bg-vintage-cream/30 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-vintage-cream/50">
        <div className="flex items-center gap-1.5">
          <Key className="h-3.5 w-3.5 text-vintage-olive" />
          <span className="text-xs font-bold text-vintage-dark/80">Gemini API Key</span>
        </div>
        {apiKey ? (
          <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
            <Check className="h-3 w-3" />
            Đã cấu hình
          </span>
        ) : (
          <span className="flex items-center gap-1 text-xs text-amber-600 font-medium">
            <AlertTriangle className="h-3 w-3" />
            Chưa có key
          </span>
        )}
      </div>

      <div className="px-3 py-2 space-y-2">
        {/* Hiển thị key đã lưu */}
        {apiKey && !showInput && (
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-white rounded-md border border-vintage-tan/20 px-2.5 py-1.5 text-xs font-mono text-vintage-dark/70 truncate">
              {showKey ? apiKey : maskedKey}
            </div>
            <button
              onClick={() => setShowKey(!showKey)}
              className="p-1.5 rounded-md hover:bg-vintage-tan/10 text-vintage-tan transition"
              title={showKey ? 'Ẩn key' : 'Hiện key'}
            >
              {showKey ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
            </button>
            <button
              onClick={handleDelete}
              className="p-1.5 rounded-md hover:bg-red-50 text-red-400 hover:text-red-600 transition"
              title="Xoá key để đổi key khác"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {/* Saved indicator */}
        {saved && (
          <p className="text-xs text-green-600 flex items-center gap-1">
            <Check className="h-3 w-3" />
            Đã lưu API key vào trình duyệt
          </p>
        )}

        {/* Input nhập key */}
        {showInput && (
          <div className="space-y-2">
            <div className="flex gap-1.5">
              <input
                type="password"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSave()}
                placeholder="Dán API Key tại đây..."
                className="flex-1 h-8 px-2.5 text-xs rounded-md border border-vintage-tan/30 bg-white
                  focus:outline-none focus:ring-2 focus:ring-vintage-olive/30 focus:border-vintage-olive
                  placeholder:text-vintage-tan/50 font-mono"
                autoComplete="off"
              />
              <button
                onClick={handleSave}
                disabled={!inputValue.trim()}
                className="h-8 px-3 text-xs font-medium rounded-md bg-vintage-olive text-white
                  hover:bg-vintage-olive/90 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                Lưu
              </button>
            </div>
            {apiKey && (
              <button
                onClick={() => setShowInput(false)}
                className="text-xs text-vintage-tan hover:text-vintage-dark transition"
              >
                ← Huỷ
              </button>
            )}
          </div>
        )}

        {/* Nút đổi key (khi đã có key) */}
        {apiKey && !showInput && (
          <button
            onClick={() => setShowInput(true)}
            className="text-xs text-vintage-olive hover:underline"
          >
            Đổi key khác
          </button>
        )}

        {/* Model Selector */}
        {models.length > 0 && (
          <div>
            <label className="text-xs font-medium text-vintage-dark/70 mb-1 flex items-center gap-1">
              <Cpu className="h-3 w-3 text-vintage-olive" />
              Gemini Model
              <button
                onClick={handleRefreshModels}
                disabled={refreshingModels}
                className="ml-auto flex items-center gap-1 text-[10px] text-vintage-olive hover:text-vintage-dark disabled:opacity-50 transition"
                title="Tải danh sách model mới nhất từ Google API"
              >
                <RefreshCw className={`h-3 w-3 ${refreshingModels ? 'animate-spin' : ''}`} />
                {refreshingModels ? 'Đang tải...' : 'Tải models'}
              </button>
            </label>
            {refreshError && (
              <p className="text-[10px] text-red-500 mb-1">{refreshError}</p>
            )}
            {refreshSuccess && (
              <p className="text-[10px] text-green-600 mb-1 flex items-center gap-1">
                <Check className="h-3 w-3" />{refreshSuccess}
              </p>
            )}
            <select
              value={selectedModel || defaultModel}
              onChange={e => handleModelChange(e.target.value)}
              className="w-full text-xs border rounded-md px-2 py-1.5 bg-white border-vintage-tan/30 focus:border-vintage-olive focus:ring-1 focus:ring-vintage-olive/30 outline-none"
            >
              {models.map(m => (
                <option key={m.id} value={m.id}>
                  {m.name} — {m.description}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Hướng dẫn lấy API key */}
        {!compact && (
          <div>
            <button
              onClick={() => setShowGuide(!showGuide)}
              className="flex items-center gap-1 text-xs text-vintage-olive hover:text-vintage-dark transition w-full"
            >
              <Sparkles className="h-3 w-3" />
              <span className="font-medium">Hướng dẫn lấy API Key miễn phí</span>
              {showGuide ? <ChevronUp className="h-3 w-3 ml-auto" /> : <ChevronDown className="h-3 w-3 ml-auto" />}
            </button>

            {showGuide && (
              <div className="mt-2 p-3 bg-white rounded-lg border border-vintage-tan/20 text-xs text-vintage-dark/80 space-y-3">
                <div>
                  <p className="font-bold text-vintage-dark mb-1 flex items-center gap-1">
                    <Sparkles className="h-3 w-3 text-vintage-olive" />
                    Google Gemini API — Miễn phí
                  </p>
                  <p className="text-vintage-tan leading-relaxed">
                    Google cung cấp miễn phí Gemini API với giới hạn rộng rãi (15 request/phút, 1 triệu token/phút). 
                    Đủ dùng cho dịch phụ đề cá nhân.
                  </p>
                </div>

                <ol className="space-y-2 list-none">
                  <li className="flex gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-vintage-olive/10 text-vintage-olive text-xs font-bold flex items-center justify-center">1</span>
                    <div>
                      <p className="font-medium text-vintage-dark">Truy cập Google AI Studio</p>
                      <a
                        href="https://aistudio.google.com/apikey"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-blue-600 hover:underline mt-0.5"
                      >
                        aistudio.google.com/apikey
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </li>
                  <li className="flex gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-vintage-olive/10 text-vintage-olive text-xs font-bold flex items-center justify-center">2</span>
                    <div>
                      <p className="font-medium text-vintage-dark">Đăng nhập Google</p>
                      <p className="text-vintage-tan">Sử dụng tài khoản Google bất kỳ (Gmail). Không cần thẻ tín dụng.</p>
                    </div>
                  </li>
                  <li className="flex gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-vintage-olive/10 text-vintage-olive text-xs font-bold flex items-center justify-center">3</span>
                    <div>
                      <p className="font-medium text-vintage-dark">Tạo API Key</p>
                      <p className="text-vintage-tan">
                        Nhấn <strong>"Create API Key"</strong> → chọn project hoặc tạo mới → 
                        nhấn <strong>"Create API key in new project"</strong>.
                      </p>
                    </div>
                  </li>
                  <li className="flex gap-2">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full bg-vintage-olive/10 text-vintage-olive text-xs font-bold flex items-center justify-center">4</span>
                    <div>
                      <p className="font-medium text-vintage-dark">Sao chép API Key</p>
                      <p className="text-vintage-tan">
                        Copy key (bắt đầu bằng <code className="px-1 py-0.5 bg-gray-100 rounded text-xs">AIza...</code>) 
                        và dán vào ô bên trên.
                      </p>
                    </div>
                  </li>
                </ol>

                <div className="p-2 bg-amber-50 rounded-md border border-amber-200/50">
                  <p className="font-medium text-amber-800 flex items-center gap-1 mb-1">
                    <AlertTriangle className="h-3 w-3" />
                    Lưu ý bảo mật
                  </p>
                  <ul className="text-amber-700 space-y-0.5 text-[11px] leading-relaxed">
                    <li>• API key chỉ lưu trong trình duyệt của bạn, <strong>không gửi lên server lưu trữ</strong>.</li>
                    <li>• Key chỉ dùng để gọi Google Gemini dịch phụ đề, không dùng mục đích khác.</li>
                    <li>• Nếu key bị rate limit hoặc lỗi, nhấn nút xoá và tạo key mới.</li>
                    <li>• Mỗi trình duyệt / thiết bị cần nhập key riêng.</li>
                  </ul>
                </div>

                <div className="p-2 bg-blue-50 rounded-md border border-blue-200/50">
                  <p className="font-medium text-blue-800 mb-1">💡 Giới hạn miễn phí (Free tier)</p>
                  <ul className="text-blue-700 space-y-0.5 text-[11px] leading-relaxed">
                    <li>• <strong>15 request/phút</strong> — đủ dịch nhiều video liên tục</li>
                    <li>• <strong>1 triệu token/phút</strong> — mỗi bản phụ đề ~2000-5000 token</li>
                    <li>• <strong>1500 request/ngày</strong> — không giới hạn thực tế cho người dùng cá nhân</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
