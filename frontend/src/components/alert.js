import React from 'react';
import PropTypes from 'prop-types';

/**
 * Alert Component to display messages with dynamic styling.
 *
 * @param {string} type - Type of the alert ('success', 'error', 'warning', 'info').
 * @param {string} message - The alert message to display.
 */
const Alert = ({ type, message }) => {
  // Determine styles dynamically based on the type
  const alertStyles = {
    success: 'bg-green-100 border-green-500 text-green-700',
    error: 'bg-red-100 border-red-500 text-red-700',
    warning: 'bg-yellow-100 border-yellow-500 text-yellow-700',
    info: 'bg-blue-100 border-blue-500 text-blue-700',
    default: 'bg-gray-100 border-gray-500 text-gray-700', // Fallback style
  };

  // Fallback to 'default' style if the type is invalid
  const selectedStyle = alertStyles[type] || alertStyles.default;

  return (
    <div
      className={`border-l-4 p-4 mb-4 ${selectedStyle}`}
      role="alert"
    >
      <p className="font-medium">{message}</p>
    </div>
  );
};

// Define prop types for validation
Alert.propTypes = {
  type: PropTypes.oneOf(['success', 'error', 'warning', 'info']),
  message: PropTypes.string.isRequired,
};

// Default props in case some are not provided
Alert.defaultProps = {
  type: 'info', // Default type is 'info'
};

export default Alert;
