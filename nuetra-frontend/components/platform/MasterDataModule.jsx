import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ArchiveRestore,
  Database,
  Download,
  Edit3,
  FileUp,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  Trash2,
  Upload,
} from 'lucide-react';

import { ownerMasterDataAPI } from '../../lib/api';
import { ActionButton, Badge, cn, ControlBar, EmptyState, ModuleFrame, Panel } from './OwnerConsolePrimitives';

const CATEGORY_TEMPLATE = {
  scope: 'GLOBAL',
  key: '',
  name: '',
  description: '',
  status: 'ACTIVE',
  sort_order: 0,
};

const ITEM_TEMPLATE = {
  code: '',
  label: '',
  description: '',
  status: 'ACTIVE',
  sort_order: 0,
  metadata_text: '{}',
};

const STATUS_FILTERS = [
  { key: '', label: 'All' },
  { key: 'ACTIVE', label: 'Active' },
  { key: 'INACTIVE', label: 'Inactive' },
  { key: 'DELETED', label: 'Deleted' },
];

function safeItems(response) {
  return Array.isArray(response?.items) ? response.items : [];
}

function csvToRows(text) {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length < 2) return [];
  const headers = lines[0].split(',').map((header) => header.trim());
  return lines.slice(1).map((line) => {
    const values = line.split(',').map((value) => value.trim());
    return headers.reduce((row, header, index) => ({ ...row, [header]: values[index] || '' }), {});
  });
}

function downloadTextFile(filename, text, type = 'text/csv;charset=utf-8') {
  const blob = new Blob([text], { type });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function TextInput({ label, value, onChange, placeholder, disabled = false, type = 'text' }) {
  return (
    <label className="block">
      <span className="text-xs font-black uppercase tracking-[0.18em] text-gray-400">{label}</span>
      <input
        type={type}
        value={value ?? ''}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="mt-2 w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-900 outline-none transition focus:border-[#237afc] disabled:bg-gray-50 disabled:text-gray-400"
      />
    </label>
  );
}

function SelectInput({ label, value, onChange, options }) {
  return (
    <label className="block">
      <span className="text-xs font-black uppercase tracking-[0.18em] text-gray-400">{label}</span>
      <select
        value={value ?? ''}
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-900 outline-none transition focus:border-[#237afc]"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function TextAreaInput({ label, value, onChange, placeholder, rows = 3 }) {
  return (
    <label className="block">
      <span className="text-xs font-black uppercase tracking-[0.18em] text-gray-400">{label}</span>
      <textarea
        value={value ?? ''}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="mt-2 w-full rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-900 outline-none transition focus:border-[#237afc]"
      />
    </label>
  );
}

function CategoryForm({ value, onChange, onSubmit, onCancel, saving, editing }) {
  return (
    <form
      className="grid gap-4 rounded-3xl border border-blue-100 bg-blue-50/40 p-5 lg:grid-cols-2"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <TextInput
        label="Category key"
        value={value.key}
        disabled={editing}
        onChange={(next) => onChange({ ...value, key: next })}
        placeholder="wellness_goals"
      />
      <TextInput
        label="Category name"
        value={value.name}
        onChange={(next) => onChange({ ...value, name: next })}
        placeholder="Wellness Goals"
      />
      <SelectInput
        label="Scope"
        value={value.scope}
        onChange={(next) => onChange({ ...value, scope: next })}
        options={[
          { value: 'GLOBAL', label: 'Global' },
          { value: 'PRODUCT', label: 'Product scoped' },
          { value: 'ORGANIZATION', label: 'Organization scoped' },
        ]}
      />
      <SelectInput
        label="Status"
        value={value.status}
        onChange={(next) => onChange({ ...value, status: next })}
        options={[
          { value: 'ACTIVE', label: 'Active' },
          { value: 'INACTIVE', label: 'Inactive' },
          { value: 'DELETED', label: 'Deleted' },
        ]}
      />
      <div className="lg:col-span-2">
        <TextAreaInput
          label="Description"
          value={value.description}
          onChange={(next) => onChange({ ...value, description: next })}
          placeholder="Explain where this master data is used."
        />
      </div>
      <div className="flex items-center gap-3 lg:col-span-2">
        <ActionButton icon={Save} label={saving ? 'Saving...' : editing ? 'Update category' : 'Create category'} tone="primary" type="submit" disabled={saving} />
        <ActionButton icon={RefreshCw} label="Cancel" onClick={onCancel} disabled={saving} />
      </div>
    </form>
  );
}

function ItemForm({ value, onChange, onSubmit, onCancel, saving, editing, disabled }) {
  return (
    <form
      className={cn('grid gap-4 rounded-3xl border border-emerald-100 bg-emerald-50/40 p-5 lg:grid-cols-2', disabled && 'opacity-60')}
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <TextInput
        label="Code"
        value={value.code}
        disabled={disabled || editing}
        onChange={(next) => onChange({ ...value, code: next })}
        placeholder="better_sleep"
      />
      <TextInput
        label="Label"
        value={value.label}
        disabled={disabled}
        onChange={(next) => onChange({ ...value, label: next })}
        placeholder="Better Sleep"
      />
      <SelectInput
        label="Status"
        value={value.status}
        onChange={(next) => onChange({ ...value, status: next })}
        options={[
          { value: 'ACTIVE', label: 'Active' },
          { value: 'INACTIVE', label: 'Inactive' },
          { value: 'DELETED', label: 'Deleted' },
        ]}
      />
      <TextInput
        label="Sort order"
        type="number"
        value={value.sort_order}
        disabled={disabled}
        onChange={(next) => onChange({ ...value, sort_order: Number(next) || 0 })}
      />
      <div className="lg:col-span-2">
        <TextAreaInput
          label="Description"
          value={value.description}
          onChange={(next) => onChange({ ...value, description: next })}
          placeholder="Optional display/help text."
        />
      </div>
      <div className="lg:col-span-2">
        <TextAreaInput
          label="Metadata JSON"
          value={value.metadata_text}
          onChange={(next) => onChange({ ...value, metadata_text: next })}
          placeholder='{"clinical": true}'
          rows={4}
        />
      </div>
      <div className="flex items-center gap-3 lg:col-span-2">
        <ActionButton icon={Save} label={saving ? 'Saving...' : editing ? 'Update item' : 'Create item'} tone="primary" type="submit" disabled={saving || disabled} />
        <ActionButton icon={RefreshCw} label="Cancel" onClick={onCancel} disabled={saving} />
      </div>
    </form>
  );
}

export default function MasterDataModule() {
  const [categories, setCategories] = useState([]);
  const [items, setItems] = useState([]);
  const [categorySearch, setCategorySearch] = useState('');
  const [itemSearch, setItemSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [includeDeleted, setIncludeDeleted] = useState(false);
  const [selectedCategoryId, setSelectedCategoryId] = useState('');
  const [categoryForm, setCategoryForm] = useState(CATEGORY_TEMPLATE);
  const [itemForm, setItemForm] = useState(ITEM_TEMPLATE);
  const [editingCategoryId, setEditingCategoryId] = useState('');
  const [editingItemId, setEditingItemId] = useState('');
  const [categoryPanelOpen, setCategoryPanelOpen] = useState(false);
  const [itemPanelOpen, setItemPanelOpen] = useState(false);
  const [importPanelOpen, setImportPanelOpen] = useState(false);
  const [importText, setImportText] = useState('category_key,code,label,status\nwellness_goals,better_energy,Better Energy,ACTIVE');
  const [loading, setLoading] = useState(true);
  const [itemsLoading, setItemsLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const selectedCategory = useMemo(
    () => categories.find((category) => category.id === selectedCategoryId) || null,
    [categories, selectedCategoryId]
  );

  const deletedCategoryCount = useMemo(
    () => categories.filter((category) => Boolean(category.deleted_at)).length,
    [categories]
  );

  const loadCategories = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await ownerMasterDataAPI.listCategories({
        search: categorySearch,
        include_deleted: includeDeleted,
        limit: 100,
      });
      const nextCategories = safeItems(response);
      setCategories(nextCategories);
      setSelectedCategoryId((current) => current || nextCategories[0]?.id || '');
    } catch (err) {
      setError(err.message || 'Unable to load master data categories.');
    } finally {
      setLoading(false);
    }
  }, [categorySearch, includeDeleted]);

  const loadItems = useCallback(async () => {
    if (!selectedCategoryId) {
      setItems([]);
      return;
    }
    setItemsLoading(true);
    setError('');
    try {
      const response = await ownerMasterDataAPI.listItems({
        category_id: selectedCategoryId,
        search: itemSearch,
        status: statusFilter,
        include_deleted: includeDeleted,
        limit: 100,
      });
      setItems(safeItems(response));
    } catch (err) {
      setError(err.message || 'Unable to load master data items.');
    } finally {
      setItemsLoading(false);
    }
  }, [includeDeleted, itemSearch, selectedCategoryId, statusFilter]);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  const resetCategoryForm = useCallback(() => {
    setCategoryForm(CATEGORY_TEMPLATE);
    setEditingCategoryId('');
    setCategoryPanelOpen(false);
  }, []);

  const resetItemForm = useCallback(() => {
    setItemForm(ITEM_TEMPLATE);
    setEditingItemId('');
    setItemPanelOpen(false);
  }, []);

  const handleCategorySubmit = useCallback(async () => {
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const payload = {
        ...categoryForm,
        key: categoryForm.key.trim(),
        name: categoryForm.name.trim(),
        description: categoryForm.description?.trim() || null,
      };
      if (editingCategoryId) {
        await ownerMasterDataAPI.updateCategory(editingCategoryId, payload);
        setNotice('Category updated successfully.');
      } else {
        const created = await ownerMasterDataAPI.createCategory(payload);
        setSelectedCategoryId(created?.id || '');
        setNotice('Category created successfully.');
      }
      resetCategoryForm();
      await loadCategories();
    } catch (err) {
      setError(err.message || 'Unable to save category.');
    } finally {
      setSaving(false);
    }
  }, [categoryForm, editingCategoryId, loadCategories, resetCategoryForm]);

  const handleItemSubmit = useCallback(async () => {
    if (!selectedCategoryId) return;
    setSaving(true);
    setError('');
    setNotice('');
    try {
      let metadata = {};
      try {
        metadata = itemForm.metadata_text ? JSON.parse(itemForm.metadata_text) : {};
      } catch {
        throw new Error('Metadata must be valid JSON.');
      }
      const payload = {
        category_id: selectedCategoryId,
        code: itemForm.code.trim(),
        label: itemForm.label.trim(),
        description: itemForm.description?.trim() || null,
        status: itemForm.status,
        sort_order: Number(itemForm.sort_order) || 0,
        metadata,
      };
      if (editingItemId) {
        await ownerMasterDataAPI.updateItem(editingItemId, payload);
        setNotice('Item updated successfully.');
      } else {
        await ownerMasterDataAPI.createItem(payload);
        setNotice('Item created successfully.');
      }
      resetItemForm();
      await loadItems();
    } catch (err) {
      setError(err.message || 'Unable to save item.');
    } finally {
      setSaving(false);
    }
  }, [editingItemId, itemForm, loadItems, resetItemForm, selectedCategoryId]);

  const editCategory = useCallback((category) => {
    setCategoryForm({
      scope: category.scope || 'GLOBAL',
      key: category.key || '',
      name: category.name || '',
      description: category.description || '',
      status: category.status || 'ACTIVE',
      sort_order: category.sort_order || 0,
    });
    setEditingCategoryId(category.id);
    setCategoryPanelOpen(true);
  }, []);

  const editItem = useCallback((item) => {
    setItemForm({
      code: item.code || '',
      label: item.label || '',
      description: item.description || '',
      status: item.status || 'ACTIVE',
      sort_order: item.sort_order || 0,
      metadata_text: JSON.stringify(item.metadata || {}, null, 2),
    });
    setEditingItemId(item.id);
    setItemPanelOpen(true);
  }, []);

  const runMutation = useCallback(async (operation, successMessage) => {
    setSaving(true);
    setError('');
    setNotice('');
    try {
      await operation();
      setNotice(successMessage);
      await loadCategories();
      await loadItems();
    } catch (err) {
      setError(err.message || 'Master data operation failed.');
    } finally {
      setSaving(false);
    }
  }, [loadCategories, loadItems]);

  const handleImport = useCallback(async () => {
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const rows = importText.trim().startsWith('[') ? JSON.parse(importText) : csvToRows(importText);
      if (!Array.isArray(rows) || rows.length === 0) throw new Error('Import requires at least one row.');
      const response = await ownerMasterDataAPI.importItems(rows);
      setNotice(`Import complete. Created ${response?.created || 0}, updated ${response?.updated || 0}.`);
      setImportPanelOpen(false);
      await loadItems();
    } catch (err) {
      setError(err.message || 'Import failed.');
    } finally {
      setSaving(false);
    }
  }, [importText, loadItems]);

  const handleExport = useCallback(async () => {
    setSaving(true);
    setError('');
    setNotice('');
    try {
      const csv = await ownerMasterDataAPI.exportItems({
        category_id: selectedCategoryId,
        include_deleted: includeDeleted,
      });
      downloadTextFile(`master-data-${selectedCategory?.key || 'items'}.csv`, csv || '');
      setNotice('Export generated successfully.');
    } catch (err) {
      setError(err.message || 'Export failed.');
    } finally {
      setSaving(false);
    }
  }, [includeDeleted, selectedCategory, selectedCategoryId]);

  return (
    <ModuleFrame
      badge="Platform services"
      title="Master Data"
      description="Reusable platform reference data for Nuetra, FitEatsy, and future Zestiva products. All records are persisted through the live platform API."
      actions={
        <>
          <ActionButton icon={RefreshCw} label="Refresh" onClick={() => { loadCategories(); loadItems(); }} disabled={loading || itemsLoading} />
          <ActionButton icon={FileUp} label="Import CSV" onClick={() => setImportPanelOpen((current) => !current)} />
          <ActionButton icon={Download} label="Export CSV" onClick={handleExport} disabled={!selectedCategoryId || saving} />
          <ActionButton icon={Plus} label="New category" tone="primary" onClick={() => setCategoryPanelOpen(true)} />
        </>
      }
    >
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-3xl bg-[#f6f9ff] p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-gray-400">Categories</p>
          <p className="mt-2 text-3xl font-black text-gray-900">{categories.length}</p>
        </div>
        <div className="rounded-3xl bg-[#f6f9ff] p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-gray-400">Selected items</p>
          <p className="mt-2 text-3xl font-black text-gray-900">{items.length}</p>
        </div>
        <div className="rounded-3xl bg-[#f6f9ff] p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-gray-400">Deleted visible</p>
          <p className="mt-2 text-3xl font-black text-gray-900">{deletedCategoryCount}</p>
        </div>
        <div className="rounded-3xl bg-[#f6f9ff] p-5">
          <p className="text-xs font-black uppercase tracking-[0.2em] text-gray-400">Feature state</p>
          <p className="mt-2 text-lg font-black text-gray-900">Acceptance gated</p>
        </div>
      </div>

      {notice ? <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-bold text-emerald-700">{notice}</div> : null}
      {error ? <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-bold text-red-700">{error}</div> : null}

      <div className="mt-6 grid gap-6 xl:grid-cols-[0.85fr_1.15fr]">
        <Panel
          title="Categories"
          subtitle="Govern reusable reference domains such as industries, goals, countries, package types, and service categories."
          action={<ActionButton icon={Plus} label="Add" onClick={() => setCategoryPanelOpen(true)} />}
        >
          <ControlBar
            searchPlaceholder="Search categories..."
            searchValue={categorySearch}
            onSearchChange={setCategorySearch}
            rightControls={
              <label className="flex items-center gap-2 rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-bold text-gray-600">
                <input type="checkbox" checked={includeDeleted} onChange={(event) => setIncludeDeleted(event.target.checked)} />
                Deleted
              </label>
            }
          />

          {categoryPanelOpen ? (
            <div className="mt-4">
              <CategoryForm
                value={categoryForm}
                onChange={setCategoryForm}
                onSubmit={handleCategorySubmit}
                onCancel={resetCategoryForm}
                saving={saving}
                editing={Boolean(editingCategoryId)}
              />
            </div>
          ) : null}

          <div className="mt-5 overflow-hidden rounded-3xl border border-gray-100">
            {loading ? (
              <div className="flex items-center justify-center gap-2 p-10 text-sm font-bold text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading categories
              </div>
            ) : categories.length === 0 ? (
              <EmptyState icon={Database} title="No categories found" description="Create the first master data category to start configuring shared platform reference data." />
            ) : (
              <table className="min-w-full divide-y divide-gray-100 text-sm">
                <thead className="sticky top-0 bg-gray-50 text-left text-xs font-black uppercase tracking-[0.18em] text-gray-400">
                  <tr>
                    <th className="px-4 py-3">Category</th>
                    <th className="px-4 py-3">Scope</th>
                    <th className="px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {categories.map((category) => (
                    <tr
                      key={category.id}
                      className={cn('cursor-pointer hover:bg-blue-50/50', selectedCategoryId === category.id && 'bg-blue-50')}
                      onClick={() => setSelectedCategoryId(category.id)}
                    >
                      <td className="px-4 py-4">
                        <p className="font-black text-gray-900">{category.name}</p>
                        <p className="text-xs font-semibold text-gray-500">{category.key}</p>
                        {category.deleted_at ? <Badge tone="red">Deleted</Badge> : null}
                      </td>
                      <td className="px-4 py-4">
                        <Badge tone={category.status === 'ACTIVE' ? 'green' : 'amber'}>{category.scope}</Badge>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2" onClick={(event) => event.stopPropagation()}>
                          <button className="rounded-xl border border-gray-200 p-2 text-gray-500 hover:text-[#237afc]" onClick={() => editCategory(category)} aria-label="Edit category">
                            <Edit3 className="h-4 w-4" />
                          </button>
                          {category.deleted_at ? (
                            <button className="rounded-xl border border-gray-200 p-2 text-gray-500 hover:text-emerald-600" onClick={() => runMutation(() => ownerMasterDataAPI.restoreCategory(category.id), 'Category restored.')} aria-label="Restore category">
                              <ArchiveRestore className="h-4 w-4" />
                            </button>
                          ) : (
                            <button className="rounded-xl border border-gray-200 p-2 text-gray-500 hover:text-red-600" onClick={() => runMutation(() => ownerMasterDataAPI.deleteCategory(category.id), 'Category deleted.')} aria-label="Delete category">
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Panel>

        <Panel
          title={selectedCategory ? `${selectedCategory.name} items` : 'Items'}
          subtitle="Create, edit, soft-delete, restore, import, and export values for the selected category."
          action={<ActionButton icon={Plus} label="Add item" onClick={() => setItemPanelOpen(true)} disabled={!selectedCategoryId} />}
        >
          <ControlBar
            searchPlaceholder="Search items..."
            searchValue={itemSearch}
            onSearchChange={setItemSearch}
            filters={STATUS_FILTERS}
            activeFilter={statusFilter}
            onFilterChange={setStatusFilter}
          />

          {itemPanelOpen ? (
            <div className="mt-4">
              <ItemForm
                value={itemForm}
                onChange={setItemForm}
                onSubmit={handleItemSubmit}
                onCancel={resetItemForm}
                saving={saving}
                editing={Boolean(editingItemId)}
                disabled={!selectedCategoryId}
              />
            </div>
          ) : null}

          {importPanelOpen ? (
            <div className="mt-4 rounded-3xl border border-violet-100 bg-violet-50/40 p-5">
              <TextAreaInput
                label="Import CSV or JSON rows"
                rows={6}
                value={importText}
                onChange={setImportText}
                placeholder="category_key,code,label,status"
              />
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-bold text-gray-700 hover:border-[#237afc] hover:text-[#237afc]">
                  <Upload className="h-4 w-4" />
                  Upload CSV
                  <input
                    type="file"
                    accept=".csv,text/csv"
                    className="hidden"
                    onChange={async (event) => {
                      const file = event.target.files?.[0];
                      if (file) setImportText(await file.text());
                    }}
                  />
                </label>
                <ActionButton icon={FileUp} label={saving ? 'Importing...' : 'Run import'} tone="primary" onClick={handleImport} disabled={saving} />
                <ActionButton icon={RefreshCw} label="Cancel" onClick={() => setImportPanelOpen(false)} />
              </div>
            </div>
          ) : null}

          <div className="mt-5 overflow-hidden rounded-3xl border border-gray-100">
            {itemsLoading ? (
              <div className="flex items-center justify-center gap-2 p-10 text-sm font-bold text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading items
              </div>
            ) : !selectedCategoryId ? (
              <EmptyState icon={Database} title="Select a category" description="Choose a category to manage its reusable values." />
            ) : items.length === 0 ? (
              <EmptyState icon={Database} title="No items found" description="Create or import items for this category." />
            ) : (
              <table className="min-w-full divide-y divide-gray-100 text-sm">
                <thead className="sticky top-0 bg-gray-50 text-left text-xs font-black uppercase tracking-[0.18em] text-gray-400">
                  <tr>
                    <th className="px-4 py-3">Code</th>
                    <th className="px-4 py-3">Label</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {items.map((item) => (
                    <tr key={item.id} className="hover:bg-blue-50/50">
                      <td className="px-4 py-4">
                        <p className="font-black text-gray-900">{item.code}</p>
                        {item.deleted_at ? <Badge tone="red">Deleted</Badge> : null}
                      </td>
                      <td className="px-4 py-4">
                        <p className="font-bold text-gray-900">{item.label}</p>
                        <p className="text-xs text-gray-500">{item.description}</p>
                      </td>
                      <td className="px-4 py-4">
                        <Badge tone={item.status === 'ACTIVE' ? 'green' : 'amber'}>{item.status}</Badge>
                      </td>
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-2">
                          <button className="rounded-xl border border-gray-200 p-2 text-gray-500 hover:text-[#237afc]" onClick={() => editItem(item)} aria-label="Edit item">
                            <Edit3 className="h-4 w-4" />
                          </button>
                          {item.deleted_at ? (
                            <button className="rounded-xl border border-gray-200 p-2 text-gray-500 hover:text-emerald-600" onClick={() => runMutation(() => ownerMasterDataAPI.restoreItem(item.id), 'Item restored.')} aria-label="Restore item">
                              <ArchiveRestore className="h-4 w-4" />
                            </button>
                          ) : (
                            <button className="rounded-xl border border-gray-200 p-2 text-gray-500 hover:text-red-600" onClick={() => runMutation(() => ownerMasterDataAPI.deleteItem(item.id), 'Item deleted.')} aria-label="Delete item">
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Panel>
      </div>
    </ModuleFrame>
  );
}
