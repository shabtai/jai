#!/usr/bin/env node
/**
 * JSON Processor - Advanced JSON transformation and validation tool
 * Processes JSON data, validates schema, and transforms structures
 */

const fs = require('fs');

class JSONProcessor {
  constructor(jsonStr) {
    this.original = jsonStr;
    this.data = null;
    this.errors = [];
  }

  parse() {
    try {
      this.data = JSON.parse(this.original);
      return true;
    } catch (e) {
      this.errors.push(`Parse error: ${e.message}`);
      return false;
    }
  }

  validate() {
    if (!this.data) return false;

    const checks = [
      this.validateStructure(),
      this.validateTypes(),
      this.validateDatatypes()
    ];

    return checks.every(c => c);
  }

  validateStructure() {
    if (typeof this.data !== 'object') {
      this.errors.push('Root must be object or array');
      return false;
    }
    return true;
  }

  validateTypes() {
    const walk = (obj, path = '') => {
      if (obj === null) return;

      if (Array.isArray(obj)) {
        obj.forEach((item, idx) => walk(item, `${path}[${idx}]`));
      } else if (typeof obj === 'object') {
        Object.keys(obj).forEach(key => {
          walk(obj[key], path ? `${path}.${key}` : key);
        });
      }
    };

    walk(this.data);
    return this.errors.length === 0;
  }

  validateDatatypes() {
    const typeMap = {};

    const checkTypes = (obj, path = '') => {
      if (obj === null) return;

      if (Array.isArray(obj)) {
        obj.forEach((item, idx) => checkTypes(item, `${path}[${idx}]`));
      } else if (typeof obj === 'object') {
        Object.keys(obj).forEach(key => {
          const value = obj[key];
          const type = typeof value;
          const fullPath = path ? `${path}.${key}` : key;

          if (!typeMap[fullPath]) {
            typeMap[fullPath] = type;
          } else if (typeMap[fullPath] !== type && value !== null) {
            this.errors.push(`Type mismatch at ${fullPath}: ${typeMap[fullPath]} vs ${type}`);
          }

          checkTypes(value, fullPath);
        });
      }
    };

    checkTypes(this.data);
    return this.errors.length === 0;
  }

  flatten() {
    const result = {};

    const flattenObj = (obj, prefix = '') => {
      if (obj === null) return;

      if (Array.isArray(obj)) {
        obj.forEach((item, idx) => {
          flattenObj(item, prefix ? `${prefix}[${idx}]` : `[${idx}]`);
        });
      } else if (typeof obj === 'object') {
        Object.keys(obj).forEach(key => {
          const newKey = prefix ? `${prefix}.${key}` : key;
          const value = obj[key];

          if (typeof value === 'object' && value !== null) {
            flattenObj(value, newKey);
          } else {
            result[newKey] = value;
          }
        });
      }
    };

    flattenObj(this.data);
    return result;
  }

  transform(transformer) {
    if (typeof transformer !== 'function') {
      this.errors.push('Transformer must be a function');
      return false;
    }

    try {
      this.data = transformer(this.data);
      return true;
    } catch (e) {
      this.errors.push(`Transform error: ${e.message}`);
      return false;
    }
  }

  getStats() {
    const stats = {
      type: Array.isArray(this.data) ? 'array' : typeof this.data,
      size: JSON.stringify(this.data).length,
      depth: this.calculateDepth(this.data),
      keys: this.countKeys(this.data),
      values: this.countValues(this.data)
    };

    return stats;
  }

  calculateDepth(obj, depth = 0) {
    if (obj === null || typeof obj !== 'object') return depth;

    if (Array.isArray(obj)) {
      return obj.length === 0 ? depth + 1 :
             Math.max(...obj.map(item => this.calculateDepth(item, depth + 1)));
    }

    const depths = Object.values(obj).map(v => this.calculateDepth(v, depth + 1));
    return depths.length === 0 ? depth + 1 : Math.max(...depths);
  }

  countKeys(obj, count = 0) {
    if (obj === null || typeof obj !== 'object') return count;

    if (Array.isArray(obj)) {
      return obj.reduce((sum, item) => sum + this.countKeys(item, 0), count);
    }

    const keys = Object.keys(obj).length;
    const nested = Object.values(obj)
      .reduce((sum, v) => sum + this.countKeys(v, 0), 0);

    return count + keys + nested;
  }

  countValues(obj, count = 0) {
    if (obj === null) return count;
    if (typeof obj !== 'object') return count + 1;

    if (Array.isArray(obj)) {
      return obj.reduce((sum, item) => sum + this.countValues(item, 0), count);
    }

    return Object.values(obj).reduce((sum, v) => sum + this.countValues(v, 0), count);
  }

  toString() {
    if (this.errors.length > 0) {
      return `Errors: ${this.errors.join(', ')}`;
    }

    const stats = this.getStats();
    const report = [];
    report.push('JSON Processing Report');
    report.push('======================');
    report.push(`Valid: ${this.data !== null}`);
    report.push(`Type: ${stats.type}`);
    report.push(`Size: ${stats.size} bytes`);
    report.push(`Depth: ${stats.depth}`);
    report.push(`Keys: ${stats.keys}`);
    report.push(`Values: ${stats.values}`);
    report.push(`Parsed Data: ${JSON.stringify(this.data, null, 2)}`);

    return report.join('\n');
  }
}

function main() {
  if (process.argv.length < 3) {
    console.log("Usage: node json_processor.js '<json_data>'");
    process.exit(1);
  }

  const jsonStr = process.argv[2];
  const processor = new JSONProcessor(jsonStr);

  if (!processor.parse()) {
    console.log(processor.toString());
    process.exit(1);
  }

  if (!processor.validate()) {
    console.log(processor.toString());
    process.exit(1);
  }

  console.log(processor.toString());
}

if (require.main === module) {
  main();
}
