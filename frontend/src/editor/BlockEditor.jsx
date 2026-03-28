import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import { buildExtensions } from './extensions';
import {
  Bold, Italic, Underline, Strikethrough, Code, Link2,
  List, ListOrdered, CheckSquare, Quote, Minus,
  Heading1, Heading2, Heading3, Table, Image as ImageIcon,
  Highlighter, AlignLeft,
} from 'lucide-react';

const SLASH_COMMANDS = [
  { label: 'Heading 1', description: 'Large section heading', icon: <Heading1 size={16} />, command: (ed) => ed.chain().focus().toggleHeading({ level: 1 }).run() },
  { label: 'Heading 2', description: 'Medium section heading', icon: <Heading2 size={16} />, command: (ed) => ed.chain().focus().toggleHeading({ level: 2 }).run() },
  { label: 'Heading 3', description: 'Small section heading', icon: <Heading3 size={16} />, command: (ed) => ed.chain().focus().toggleHeading({ level: 3 }).run() },
  { label: 'Bullet List', description: 'Unordered list', icon: <List size={16} />, command: (ed) => ed.chain().focus().toggleBulletList().run() },
  { label: 'Numbered List', description: 'Ordered list', icon: <ListOrdered size={16} />, command: (ed) => ed.chain().focus().toggleOrderedList().run() },
  { label: 'Task List', description: 'Checklist with checkboxes', icon: <CheckSquare size={16} />, command: (ed) => ed.chain().focus().toggleTaskList().run() },
  { label: 'Blockquote', description: 'Capture a quote', icon: <Quote size={16} />, command: (ed) => ed.chain().focus().toggleBlockquote().run() },
  { label: 'Code Block', description: 'Syntax-highlighted code', icon: <Code size={16} />, command: (ed) => ed.chain().focus().toggleCodeBlock().run() },
  { label: 'Divider', description: 'Horizontal separator', icon: <Minus size={16} />, command: (ed) => ed.chain().focus().setHorizontalRule().run() },
  { label: 'Table', description: 'Insert a table', icon: <Table size={16} />, command: (ed) => ed.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run() },
];

function SlashMenu({ items, onSelect, position }) {
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((i) => (i + 1) % items.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((i) => (i - 1 + items.length) % items.length);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        onSelect(items[selectedIndex]);
      } else if (e.key === 'Escape') {
        onSelect(null);
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [items, selectedIndex, onSelect]);

  return (
    <div
      className="slash-menu fixed z-40 shadow-2xl"
      style={{ top: position.y, left: position.x }}
    >
      {items.map((item, i) => (
        <div
          key={item.label}
          className={`slash-menu-item ${i === selectedIndex ? 'is-selected' : ''}`}
          onMouseEnter={() => setSelectedIndex(i)}
          onClick={() => onSelect(item)}
        >
          <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center text-gray-700 flex-shrink-0">
            {item.icon}
          </div>
          <div>
            <div className="text-sm font-medium text-gray-900">{item.label}</div>
            <div className="text-xs text-gray-500">{item.description}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function Toolbar({ editor }) {
  if (!editor) return null;

  const btn = (action, Icon, isActive, title) => (
    <button
      key={title}
      onClick={action}
      title={title}
      className={`p-1.5 rounded hover:bg-gray-100 transition-colors ${
        isActive ? 'bg-gray-200 text-indigo-700' : 'text-gray-600'
      }`}
    >
      <Icon size={15} />
    </button>
  );

  return (
    <div className="flex flex-wrap items-center gap-0.5 px-4 py-2 border-b border-gray-100 bg-white sticky top-0 z-10">
      {btn(() => editor.chain().focus().toggleBold().run(), Bold, editor.isActive('bold'), 'Bold')}
      {btn(() => editor.chain().focus().toggleItalic().run(), Italic, editor.isActive('italic'), 'Italic')}
      {btn(() => editor.chain().focus().toggleUnderline().run(), Underline, editor.isActive('underline'), 'Underline')}
      {btn(() => editor.chain().focus().toggleStrike().run(), Strikethrough, editor.isActive('strike'), 'Strikethrough')}
      {btn(() => editor.chain().focus().toggleCode().run(), Code, editor.isActive('code'), 'Inline Code')}
      {btn(() => editor.chain().focus().toggleHighlight().run(), Highlighter, editor.isActive('highlight'), 'Highlight')}
      <div className="w-px h-4 bg-gray-200 mx-1" />
      {btn(() => editor.chain().focus().toggleHeading({ level: 1 }).run(), Heading1, editor.isActive('heading', { level: 1 }), 'Heading 1')}
      {btn(() => editor.chain().focus().toggleHeading({ level: 2 }).run(), Heading2, editor.isActive('heading', { level: 2 }), 'Heading 2')}
      {btn(() => editor.chain().focus().toggleHeading({ level: 3 }).run(), Heading3, editor.isActive('heading', { level: 3 }), 'Heading 3')}
      <div className="w-px h-4 bg-gray-200 mx-1" />
      {btn(() => editor.chain().focus().toggleBulletList().run(), List, editor.isActive('bulletList'), 'Bullet List')}
      {btn(() => editor.chain().focus().toggleOrderedList().run(), ListOrdered, editor.isActive('orderedList'), 'Ordered List')}
      {btn(() => editor.chain().focus().toggleTaskList().run(), CheckSquare, editor.isActive('taskList'), 'Task List')}
      {btn(() => editor.chain().focus().toggleBlockquote().run(), Quote, editor.isActive('blockquote'), 'Blockquote')}
      <div className="w-px h-4 bg-gray-200 mx-1" />
      {btn(() => editor.chain().focus().toggleCodeBlock().run(), Code, editor.isActive('codeBlock'), 'Code Block')}
    </div>
  );
}

export default function BlockEditor({ initialContent, onChange, placeholder, readOnly = false }) {
  const [slashMenu, setSlashMenu] = useState(null);
  const [slashQuery, setSlashQuery] = useState('');
  const editorRef = useRef(null);

  const filteredCommands = SLASH_COMMANDS.filter((c) =>
    c.label.toLowerCase().includes(slashQuery.toLowerCase())
  );

  const editor = useEditor({
    extensions: buildExtensions(placeholder),
    content: initialContent || '',
    editable: !readOnly,
    onUpdate: ({ editor }) => {
      const json = editor.getJSON();
      const text = editor.getText();
      onChange?.({ blocks: json, plain_text: text });
      checkForSlashCommand(editor);
    },
  });

  // Update content when initialContent changes externally (on page switch)
  useEffect(() => {
    if (editor && initialContent) {
      const current = JSON.stringify(editor.getJSON());
      const incoming = typeof initialContent === 'string'
        ? initialContent
        : JSON.stringify(initialContent);
      if (current !== incoming) {
        editor.commands.setContent(initialContent, false);
      }
    }
  }, [initialContent]);

  const checkForSlashCommand = useCallback((ed) => {
    const { from } = ed.state.selection;
    const textBefore = ed.state.doc.textBetween(Math.max(0, from - 20), from, '\n');
    const slashMatch = textBefore.match(/\/(\w*)$/);

    if (slashMatch) {
      setSlashQuery(slashMatch[1]);
      const coords = ed.view.coordsAtPos(from);
      setSlashMenu({ x: coords.left, y: coords.bottom + 4 });
    } else {
      setSlashMenu(null);
      setSlashQuery('');
    }
  }, []);

  const handleSlashSelect = useCallback(
    (item) => {
      setSlashMenu(null);
      setSlashQuery('');
      if (!item || !editor) return;

      // Delete the "/" trigger text
      const { from } = editor.state.selection;
      const textBefore = editor.state.doc.textBetween(Math.max(0, from - 20), from, '\n');
      const slashMatch = textBefore.match(/\/(\w*)$/);
      if (slashMatch) {
        const deleteFrom = from - slashMatch[0].length;
        editor.chain().focus().deleteRange({ from: deleteFrom, to: from }).run();
      }

      item.command(editor);
    },
    [editor]
  );

  const charCount = editor?.storage.characterCount?.characters() ?? 0;
  const wordCount = editor?.storage.characterCount?.words() ?? 0;

  return (
    <div className="flex flex-col h-full" ref={editorRef}>
      {!readOnly && <Toolbar editor={editor} />}
      <div className="flex-1 overflow-y-auto">
        <EditorContent
          editor={editor}
          className="prose prose-slate max-w-none px-8 py-6 min-h-full focus:outline-none"
        />
      </div>
      {!readOnly && (
        <div className="px-8 py-1.5 border-t border-gray-100 flex items-center gap-4 text-xs text-gray-400">
          <span>{wordCount} words</span>
          <span>{charCount} characters</span>
        </div>
      )}
      {slashMenu && filteredCommands.length > 0 && (
        <SlashMenu
          items={filteredCommands}
          position={slashMenu}
          onSelect={handleSlashSelect}
        />
      )}
    </div>
  );
}
