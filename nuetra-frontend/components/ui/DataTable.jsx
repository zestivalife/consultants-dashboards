import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown, Search, Download } from 'lucide-react';
import LoadingState from './LoadingState';
import EmptyState from './EmptyState';

/**
 * DataTable - Modern table with sorting, filtering, search
 * Displays tabular data with rich interactions
 */
const DataTable = ({
  columns = [],
  data = [],
  loading = false,
  searchable = true,
  sortable = true,
  exportable = false,
  onExport,
  onRowClick,
  emptyMessage = 'No data available',
  className = '',
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  // Search and sort logic
  const processedData = useMemo(() => {
    let filtered = [...data];

    // Search
    if (searchTerm) {
      filtered = filtered.filter((row) =>
        columns.some((col) => {
          const value = col.accessor ? col.accessor(row) : row[col.key];
          return String(value).toLowerCase().includes(searchTerm.toLowerCase());
        })
      );
    }

    // Sort
    if (sortConfig.key) {
      filtered.sort((a, b) => {
        const col = columns.find((c) => c.key === sortConfig.key);
        const aValue = col.accessor ? col.accessor(a) : a[sortConfig.key];
        const bValue = col.accessor ? col.accessor(b) : b[sortConfig.key];

        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  }, [data, searchTerm, sortConfig, columns]);

  const handleSort = (key) => {
    if (!sortable) return;
    
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  if (loading) {
    return <LoadingState type="table" rows={5} />;
  }

  return (
    <div className={`bg-white rounded-xl border border-gray-200 ${className}`}>
      {/* Table Header */}
      {(searchable || exportable) && (
        <div className="p-4 border-b border-gray-200 flex items-center justify-between gap-4 flex-wrap">
          {searchable && (
            <div className="relative flex-1 min-w-[250px]">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#64ae00] focus:border-transparent"
              />
            </div>
          )}
          {exportable && (
            <button
              onClick={onExport}
              className="btn-secondary flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
          )}
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto custom-scrollbar">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider ${
                    col.sortable !== false && sortable ? 'cursor-pointer hover:bg-gray-100' : ''
                  }`}
                  onClick={() =>
                    col.sortable !== false && sortable && handleSort(col.key)
                  }
                >
                  <div className="flex items-center gap-2">
                    <span>{col.label}</span>
                    {sortable && col.sortable !== false && sortConfig.key === col.key && (
                      sortConfig.direction === 'asc' ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {processedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-6 py-12">
                  <EmptyState
                    iconType="search"
                    title={searchTerm ? 'No results found' : emptyMessage}
                    description={
                      searchTerm
                        ? 'Try adjusting your search terms'
                        : 'Data will appear here when available'
                    }
                  />
                </td>
              </tr>
            ) : (
              processedData.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className={`hover:bg-gray-50 transition-colors ${
                    onRowClick ? 'cursor-pointer' : ''
                  }`}
                  onClick={() => onRowClick && onRowClick(row)}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className="px-6 py-4 text-sm text-gray-900 whitespace-nowrap"
                    >
                      {col.render
                        ? col.render(row)
                        : col.accessor
                        ? col.accessor(row)
                        : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Table Footer */}
      {processedData.length > 0 && (
        <div className="px-6 py-3 border-t border-gray-200 text-sm text-gray-600">
          Showing {processedData.length} of {data.length} entries
        </div>
      )}
    </div>
  );
};

export default DataTable;

