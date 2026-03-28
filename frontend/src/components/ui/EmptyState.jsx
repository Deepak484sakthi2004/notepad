import React from 'react';
import { classNames } from '@/utils/helpers';

export default function EmptyState({
  icon,
  title,
  description,
  action,
  className = '',
}) {
  return (
    <div
      className={classNames(
        'flex flex-col items-center justify-center py-16 px-6 text-center',
        className
      )}
    >
      {icon && (
        <div className="mb-4 text-gray-300 flex items-center justify-center">
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-gray-700 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-gray-500 mb-5 max-w-xs">{description}</p>
      )}
      {action}
    </div>
  );
}
