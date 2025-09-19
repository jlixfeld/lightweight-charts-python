import js from '@eslint/js';
import globals from 'globals';

export default [
  js.configs.recommended,
  {
    files: ["app/static/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "script",
      globals: {
        ...globals.browser,
        console: "readonly",
        fetch: "readonly",
        URLSearchParams: "readonly",
        setTimeout: "readonly",
        document: "readonly",
        window: "readonly"
      }
    },
    rules: {
      // Possible Problems
      "no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
      "no-undef": "error",
      "no-unreachable": "error",

      // Suggestions
      "prefer-const": "error",
      "no-var": "error",
      "eqeqeq": ["error", "always"],
      "curly": ["error", "all"],
      "no-console": "warn",

      // Layout & Formatting (handled by Prettier)
      "indent": "off",
      "quotes": "off",
      "semi": "off",
      "comma-dangle": "off",
      "max-len": "off",

      // Best Practices
      "no-eval": "error",
      "no-implied-eval": "error",
      "no-new-func": "error",
      "no-script-url": "error",
      "prefer-template": "error",
      "no-useless-concat": "error",

      // ES6+
      "arrow-spacing": "error",
      "no-duplicate-imports": "error",
      "prefer-arrow-callback": "error"
    }
  },
  {
    files: ["app/templates/**/*.html"],
    languageOptions: {
      globals: {
        ...globals.browser
      }
    },
    rules: {
      // Minimal rules for HTML files
      "no-undef": "off",
      "no-unused-vars": "off"
    }
  }
];