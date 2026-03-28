import React from 'react';
import { classNames } from '@/utils/helpers';

export default function Input({
  label,
  error,
  hint,
  className = '',
  containerClassName = '',
  icon,
  ...props
}) {
  return (
    <div className={classNames('flex flex-col gap-1', containerClassName)}>
      {label && (
        <label className="text-sm font-medium text-gray-700">{label}</label>
      )}
      <div className="relative">
        {icon && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            {icon}
          </span>
        )}
        <input
          className={classNames(
            'w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-900 placeholder-gray-400 transition-colors focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-200 disabled:bg-gray-50 disabled:text-gray-500',
            icon && 'pl-9',
            error && 'border-red-400 focus:border-red-400 focus:ring-red-200',
            className
          )}
          {...props}
        />
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
      {hint && !error && <p className="text-xs text-gray-500">{hint}</p>}
    </div>
  );
}
