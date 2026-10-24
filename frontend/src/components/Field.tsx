import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

interface FieldProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

/** Floating-label input (Netflix-style) with password reveal. */
export const Field: React.FC<FieldProps> = ({ label, value, onChange, type = 'text', id, ...rest }) => {
  const [show, setShow] = useState(false);
  const isPassword = type === 'password';
  const inputId = id || `field-${label.replace(/\s+/g, '-').toLowerCase()}`;

  return (
    <div className="relative">
      <input
        id={inputId}
        type={isPassword && show ? 'text' : type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder=" "
        {...rest}
        className="peer h-14 w-full rounded-md border border-white/20 bg-black/40 px-4 pb-1 pt-5 text-[15px] text-white outline-none transition-colors placeholder-transparent focus:border-white/70 focus:bg-black/60"
      />
      <label
        htmlFor={inputId}
        className="pointer-events-none absolute left-4 top-1/2 origin-left -translate-y-1/2 text-[15px] text-zinc-400 transition-all duration-200
          peer-focus:top-3.5 peer-focus:scale-[0.78] peer-[:not(:placeholder-shown)]:top-3.5 peer-[:not(:placeholder-shown)]:scale-[0.78]"
      >
        {label}
      </label>
      {isPassword && (
        <button
          type="button"
          onClick={() => setShow((s) => !s)}
          aria-label={show ? 'Hide password' : 'Show password'}
          className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-zinc-400 transition-colors hover:text-white"
        >
          {show ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
        </button>
      )}
    </div>
  );
};
