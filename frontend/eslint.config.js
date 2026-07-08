import js from "@eslint/js";
import reactPlugin from "eslint-plugin-react";
import reactHooksPlugin from "eslint-plugin-react-hooks";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";

export default [
    js.configs.recommended,
    {
        files: ["**/*.{js,jsx,mjs,cjs,ts,tsx}"],
        plugins: {
            react: reactPlugin,
            "react-hooks": reactHooksPlugin,
            "@typescript-eslint": tseslint,
        },
        languageOptions: {
            parser: tsParser,
            parserOptions: {
                ecmaFeatures: {
                    jsx: true,
                },
            },
        },
        rules: {
            "react/react-in-jsx-scope": "off",
            "no-unused-vars": "off",
            "@typescript-eslint/no-unused-vars": "off"
        },
    },
];
