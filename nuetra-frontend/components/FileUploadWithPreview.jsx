import React, { useState, useRef } from 'react';
import { Upload, X, FileText, Image, AlertCircle, Loader, CheckCircle } from 'lucide-react';
import { dietPlanAPI } from '../utils/api';

const FileUploadWithPreview = ({ dietPlanId, onComplete, initialFiles = [], isLoading, setIsLoading }) => {
  const [files, setFiles] = useState(initialFiles);
  const [dragActive, setDragActive] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [errors, setErrors] = useState({});
  const fileInputRef = useRef(null);

  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  const MAX_FILES = 5;
  const ALLOWED_TYPES = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
  const ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpeg', '.jpg'];

  const validateFile = (file) => {
    const errors = [];

    // Check file type
    if (!ALLOWED_TYPES.includes(file.type)) {
      errors.push('Only PDF, PNG, and JPEG files are allowed');
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      errors.push('File size must be less than 10MB');
    }

    return errors;
  };

  const handleFiles = (newFiles) => {
    const fileArray = Array.from(newFiles);
    const validFiles = [];
    const fileErrors = {};

    // Check total file count
    if (files.length + fileArray.length > MAX_FILES) {
      setErrors({ general: `Maximum ${MAX_FILES} files allowed` });
      return;
    }

    fileArray.forEach((file, index) => {
      const fileValidationErrors = validateFile(file);
      
      if (fileValidationErrors.length > 0) {
        fileErrors[`file_${index}`] = fileValidationErrors;
      } else {
        // Create preview URL for images
        const fileWithPreview = {
          file,
          id: Date.now() + index,
          name: file.name,
          size: file.size,
          type: file.type,
          preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
        };
        validFiles.push(fileWithPreview);
      }
    });

    if (Object.keys(fileErrors).length > 0) {
      setErrors(fileErrors);
    } else {
      setErrors({});
      setFiles(prev => [...prev, ...validFiles]);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(e.target.files);
    }
  };

  const removeFile = (fileId) => {
    setFiles(prev => {
      const updated = prev.filter(f => f.id !== fileId);
      // Revoke object URL to prevent memory leaks
      const fileToRemove = prev.find(f => f.id === fileId);
      if (fileToRemove?.preview) {
        URL.revokeObjectURL(fileToRemove.preview);
      }
      return updated;
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type) => {
    if (type.startsWith('image/')) {
      return <Image className="h-8 w-8 text-blue-600" />;
    } else if (type === 'application/pdf') {
      return <FileText className="h-8 w-8 text-red-600" />;
    }
    return <FileText className="h-8 w-8 text-gray-600" />;
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setErrors({ general: 'Please select at least one file to upload' });
      return;
    }

    setIsLoading(true);
    setUploadProgress(0);
    setErrors({});

    try {
      // Validate file objects
      const fileArray = files.map(f => f.file);
      
      if (fileArray.some(f => !(f instanceof File))) {
        throw new Error('Invalid file format detected');
      }

      // Use the API client's uploadFiles method which handles the upload
      const result = await dietPlanAPI.uploadFiles(dietPlanId, fileArray);
      
      console.log('Files uploaded successfully:', result);
      
      // Clean up preview URLs
      files.forEach(file => {
        if (file.preview) {
          URL.revokeObjectURL(file.preview);
        }
      });
      
      // Extract plan ID from result or use existing
      const planId = result?.dietPlanId || result?.id || dietPlanId;
      
      if (!planId) {
        console.warn('Warning: No diet plan ID available after file upload');
      }

      setUploadProgress(100);
      
      setTimeout(() => {
        onComplete({
          dietPlanId: planId || dietPlanId,
          uploadedFiles: result?.files || fileArray.map((f, idx) => ({
            id: idx,
            name: f.name,
            size: f.size,
            type: f.type,
            file_url: result?.file_url || `file_${idx}`
          })),
          message: 'Files uploaded successfully'
        });
      }, 500);
      
    } catch (error) {
      console.error('Upload error:', error);
      
      // Handle different types of errors
      let errorMessage = 'Upload failed. Please try again.';
      
      if (error.message?.includes('Invalid file') || error.message?.includes('No files')) {
        errorMessage = error.message;
      } else if (error.message?.includes('network') || !navigator.onLine) {
        errorMessage = 'Network error. Please check your internet connection and try again.';
      } else if (error.status === 413) {
        errorMessage = 'Files too large. Please reduce file size and try again.';
      } else if (error.status === 401 || error.status === 403) {
        errorMessage = 'Session expired. Please refresh the page and try again.';
      } else if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setErrors({ general: errorMessage });
      setUploadProgress(0);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    onComplete({
      uploadedFiles: []
    });
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-medium text-gray-900 mb-2">Upload Supporting Documents</h3>
        <p className="text-sm text-gray-600">
          Upload any relevant documents such as medical reports, previous diet plans, or lab results (optional)
        </p>
      </div>

      {/* File Upload Area */}
      <div
        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ALLOWED_EXTENSIONS.join(',')}
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        
        <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-lg font-medium text-gray-900 mb-2">
          Drop files here or click to browse
        </p>
        <p className="text-sm text-gray-600 mb-4">
          PDF, PNG, JPEG files up to 10MB each (max {MAX_FILES} files)
        </p>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Select Files
        </button>
      </div>

      {/* File Validation Errors */}
      {Object.keys(errors).length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center mb-2">
            <AlertCircle className="h-5 w-5 text-red-600 mr-2" />
            <h4 className="text-sm font-medium text-red-800">Upload Errors</h4>
          </div>
          {errors.general && (
            <p className="text-sm text-red-700 mb-2">{errors.general}</p>
          )}
          {Object.entries(errors).filter(([key]) => key.startsWith('file_')).map(([key, fileErrors]) => (
            <div key={key} className="text-sm text-red-700">
              {fileErrors.map((error, index) => (
                <p key={index}>• {error}</p>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* File Preview List */}
      {files.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-900">Selected Files ({files.length}/{MAX_FILES})</h4>
          {files.map((fileData) => (
            <div key={fileData.id} className="flex items-center p-3 bg-gray-50 rounded-lg">
              <div className="flex-shrink-0 mr-3">
                {fileData.preview ? (
                  <img
                    src={fileData.preview}
                    alt={fileData.name}
                    className="h-12 w-12 object-cover rounded"
                  />
                ) : (
                  getFileIcon(fileData.type)
                )}
              </div>
              
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {fileData.name}
                </p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(fileData.size)}
                </p>
              </div>
              
              <button
                onClick={() => removeFile(fileData.id)}
                className="flex-shrink-0 ml-3 p-1 text-gray-400 hover:text-red-600 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Progress Bar (only shown during upload) */}
      {isLoading && uploadProgress > 0 && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm font-medium text-blue-700">Uploading files...</span>
            <span className="text-sm font-medium text-blue-700">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div 
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-in-out" 
              style={{ width: `${uploadProgress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-between">
        <button
          onClick={handleSkip}
          disabled={isLoading}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50"
        >
          Skip this step
        </button>
        
        <button
          onClick={handleUpload}
          disabled={isLoading || files.length === 0}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
        >
          {isLoading && <Loader className="h-4 w-4 mr-2 animate-spin" />}
          {files.length > 0 ? 'Upload Files & Continue' : 'Continue'}
        </button>
      </div>

      {/* File Requirements */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-800 mb-2">File Requirements</h4>
        <ul className="text-xs text-blue-700 space-y-1">
          <li>• Supported formats: PDF, PNG, JPEG</li>
          <li>• Maximum file size: 10MB per file</li>
          <li>• Maximum files: {MAX_FILES} files total</li>
          <li>• Files are optional but can help your dietician create a better plan</li>
        </ul>
      </div>
    </div>
  );
};

export default FileUploadWithPreview;