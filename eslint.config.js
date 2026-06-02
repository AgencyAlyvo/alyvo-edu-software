import eslintConfigPrettier from 'eslint-config-prettier'
import eslintPluginPrettier from 'eslint-plugin-prettier'
import eslintPluginTypeScript from '@typescript-eslint/eslint-plugin'
import eslintPluginStylistic from '@stylistic/eslint-plugin'
import eslintPluginJSDoc from 'eslint-plugin-jsdoc'
import eslintPluginUnusedImports from 'eslint-plugin-unused-imports'
import eslintPluginVue from 'eslint-plugin-vue'
import eslintParserVue from 'vue-eslint-parser'
import eslintParserTypeScript from '@typescript-eslint/parser'

// Configuration principale
const mainConfig = {
  files: [
    // Nuxt app
    'src-nuxt/app/**/*.{ts,tsx,vue}',

    // Nuxt server / shared / local modules
    'src-nuxt/server/**/*.{ts,tsx}',
    'src-nuxt/shared/**/*.{ts,tsx}',
    'src-nuxt/modules/**/*.{ts,tsx}',

    // Layers Nuxt locaux
    'src-nuxt/layers/**/*.{ts,tsx,vue}',

    // Core métier
    'src-core/**/*.{ts,tsx}',

    // Tests
    'tests/**/*.{ts,tsx}',
    'cypress/**/*.{ts,tsx}',

    // Fichiers de config
    'src-nuxt/nuxt.config.ts',
    'vitest.config.ts',
    'tailwind.config.ts',
    'cypress.config.ts',
  ],
  plugins: {
    '@typescript-eslint': eslintPluginTypeScript,
    'eslint-plugin-prettier': eslintPluginPrettier,
    'eslint-plugin-unused-imports': eslintPluginUnusedImports,
    'eslint-plugin-jsdoc': eslintPluginJSDoc,
    '@stylistic-eslint-plugin': eslintPluginStylistic,
    'eslint-plugin-vue': eslintPluginVue,
  },
  rules: {
    /**
     * ESLINT PLUGIN : eslint-plugin-prettier
     */
    // Active les règles de formatage de Prettier comme des règles ESLint.
    'eslint-plugin-prettier/prettier': 'error',

    /**
     * ESLINT PLUGIN : eslint-plugin-unused-imports
     */
    // Prévient les imports inutilisés, aidant à garder le code propre
    // et à réduire la taille du bundle en éliminant les dépendances inutiles.
    'eslint-plugin-unused-imports/no-unused-imports': 'error',

    // Prévient les variables inutilisées, aidant à garder le code propre
    'eslint-plugin-unused-imports/no-unused-vars': [
      'error',
      {
        vars: 'all', // Vérifie les variables non utilisées dans le code.
        varsIgnorePattern: '^_', // Ignore les variables qui commencent par un underscore.
        args: 'after-used', // Vérifie les arguments de fonction non utilisés après le dernier argument utilisé.
        argsIgnorePattern: '^_', // Ignore les arguments de fonction qui commencent par un underscore.
      },
    ],

    /**
     * ESLINT PLUGIN : eslint-plugin-vue
     */

    /**
     * ESLINT PLUGIN : typescript-eslint/eslint-plugin
     */
    // Avec des options pour forcer l'explicité des constructeurs:
    // Cela peut aider à garantir que les constructeurs de classe sont explicitement marqués comme public, private, ou protected
    '@typescript-eslint/explicit-member-accessibility': [
      'error',
      { accessibility: 'explicit', overrides: { constructors: 'no-public' } },
    ],

    // Encourage l'utilisation d'initialiseurs avec les énumérations pour garantir que chaque membre de l'énumération
    // a une valeur explicite, améliorant ainsi la clarté et la prévisibilité du code.
    '@typescript-eslint/prefer-enum-initializers': 'error',

    // Dans un projet TypeScript, il est préférable d'utiliser des importations de modules ES6 plutôt
    // que l'ancienne syntaxe require() de CommonJS, pour une meilleure cohérence et interopérabilité des modules.
    '@typescript-eslint/no-var-requires': 'error',

    // Encourage l'utilisation de la syntaxe import type {...} pour les importations de types uniquement.
    // Réduit le coût de l'importation de types en TypeScript, car les importations de types ne sont pas incluses dans le code généré.
    '@typescript-eslint/consistent-type-imports': 'error',

    // Cette règle vous aide à identifier les fonctions async qui n'utilisent pas await. Cela peut être utile pour éviter des erreurs
    // où une fonction est marquée comme async sans raison, ce qui peut conduire à des comportements inattendus ou à une consommation inutile de ressources.
    '@typescript-eslint/require-await': 'error',

    // Avertit contre l'utilisation incorrecte des promesses, par exemple, dans les callbacks
    // sans await ou quand une fonction attend une promesse mais reçoit un type non-promise.
    '@typescript-eslint/no-misused-promises': 'error',

    // Interdit les conditions qui sont toujours vraies ou toujours fausses en fonction des types des expressions impliquées.
    // Cela peut aider à prévenir les erreurs logiques basées sur une mauvaise compréhension des types possibles dans une expression.
    '@typescript-eslint/no-unnecessary-condition': 'error',

    // Encourage l'utilisation de la chaîne optionnelle (?.) pour accéder aux propriétés ou
    // appeler des méthodes sur des objets qui peuvent être null ou undefined, réduisant ainsi le besoin de vérifications explicites de nullité.
    '@typescript-eslint/prefer-optional-chain': 'error',

    // Encourage l'utilisation de readonly pour marquer les membres de classe qui ne devraient pas être modifiés après l'initialisation.
    '@typescript-eslint/prefer-readonly': 'error',

    // Exige que chaque fonction déclare explicitement son type de retour.
    '@typescript-eslint/explicit-function-return-type': ['error'],

    // Désactive l'inférence de type explicite pour les variables et les membres de classe.
    '@typescript-eslint/no-inferrable-types': 0,

    '@typescript-eslint/typedef': [
      'error',
      {
        arrowParameter: true, // Oblige à déclarer le type de paramètre pour les fonctions fléchées.
        variableDeclaration: true, // Oblige à déclarer le type de variable lors de l'initialisation.
      },
    ],

    /**
     * ESLINT PLUGIN : stylistic-eslint-plugin
     */
    // Cette règle impose des espaces autour des annotations de type pour une meilleure lisibilité.
    '@stylistic-eslint-plugin/type-annotation-spacing': 'error',

    /**
     * ESLINT PLUGIN : eslint-plugin-jsdoc
     */
    // Vérifie que le JSDOC est présent pour les fonctions, les méthodes, les classes, les fonctions fléchées et les expressions de fonction.
    'eslint-plugin-jsdoc/require-jsdoc': [
      'error',
      {
        require: {
          FunctionDeclaration: true,
          MethodDefinition: true,
          ClassDeclaration: true,
          ArrowFunctionExpression: true,
          FunctionExpression: true,
        },
        contexts: ['TSTypeAliasDeclaration', 'TSInterfaceDeclaration'],
      },
    ],
  },
  settings: {
    'import/resolver': {
      typescript: {
        alwaysTryTypes: true,
        project: ['./tsconfig.json', './src-nuxt/tsconfig.json'],
      },
    },
  },
  languageOptions: {
    parser: eslintParserVue,
    parserOptions: {
      extraFileExtensions: ['.vue'],
      parser: eslintParserTypeScript,
      project: ['./tsconfig.json', './src-nuxt/tsconfig.json'],
      tsconfigRootDir: import.meta.dirname,
      ecmaVersion: 'latest',
      sourceType: 'module',
    },
    globals: {
      browser: true,
      node: true,
    },
  },
}

// Configuration pour l'ignorance globale
// Bug issue : https://github.com/eslint/eslint/issues/17400
const ignoreConfig = {
  ignores: [
    // Nuxt / Nitro générés à la racine éventuelle
    '.nuxt/**',
    '.output/**',
    '.nitro/**',
    '.data/**',
    '.cache/**',

    // Nuxt / Nitro générés dans src-nuxt
    'src-nuxt/.nuxt/**',
    'src-nuxt/.output/**',
    'src-nuxt/.nitro/**',
    'src-nuxt/.data/**',
    'src-nuxt/.cache/**',
    'src-nuxt/node_modules/**',

    // Build outputs
    'dist/**',
    'dist-ssr/**',
    'coverage/**',

    // Dépendances
    'node_modules/**',

    // Rapports de tests
    'tests/unit/test-reports/**',
    'tests/e2e/test-reports/**',

    '*.config.{js,cjs,mjs,ts}',
  ],
}

/**
 * @type {import("eslint").Linter.Config}
 *
 * Exportation combinée des configurations
 * eslint.config.{js,mjs,cjs} nouvelle syntaxe depuis la version >= 8.57
 */
export default [mainConfig, ignoreConfig, eslintPluginJSDoc.configs['flat/recommended'], eslintConfigPrettier]
