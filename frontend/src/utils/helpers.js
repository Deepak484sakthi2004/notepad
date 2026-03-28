import { formatDistanceToNow, format } from 'date-fns';

export function timeAgo(dateStr) {
  if (!dateStr) return '';
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true });
  } catch {
    return '';
  }
}

export function formatDate(dateStr, pattern = 'MMM d, yyyy') {
  if (!dateStr) return '';
  try {
    return format(new Date(dateStr), pattern);
  } catch {
    return '';
  }
}

export function buildPageTree(pages) {
  if (!pages || pages.length === 0) return [];

  const map = {};
  pages.forEach((p) => {
    map[p.id] = { ...p, children: [] };
  });

  const roots = [];
  pages.forEach((p) => {
    if (p.parent_page_id && map[p.parent_page_id]) {
      map[p.parent_page_id].children.push(map[p.id]);
    } else {
      roots.push(map[p.id]);
    }
  });

  const sort = (nodes) => {
    nodes.sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));
    nodes.forEach((n) => sort(n.children));
    return nodes;
  };

  return sort(roots);
}

export function truncate(str, max = 60) {
  if (!str) return '';
  if (str.length <= max) return str;
  return str.slice(0, max).trimEnd() + '…';
}

export function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function difficultyLabel(n) {
  return { 1: 'Easy', 2: 'Medium', 3: 'Hard' }[n] ?? 'Medium';
}

export function difficultyColor(n) {
  return (
    { 1: 'text-green-600 bg-green-50', 2: 'text-yellow-600 bg-yellow-50', 3: 'text-red-600 bg-red-50' }[n] ??
    'text-gray-600 bg-gray-50'
  );
}

export function qualityColor(q) {
  if (q >= 4) return 'text-green-600';
  if (q >= 2) return 'text-yellow-600';
  return 'text-red-600';
}
