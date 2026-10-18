import {t} from './i18n.mjs';
/** Display contracts, not IFC validity or repair-success decisions. */
const nonSolid = new Set(['IfcOpeningElement', 'IfcSpace', 'IfcAnnotation']);
export function coverage(products, renderedIds) {
  const expected = products.filter(p => p.representation && !nonSolid.has(p.type));
  return {
    expected: expected.length,
    rendered: expected.filter(p => renderedIds.has(p.id)).length,
    missing: expected.filter(p => !renderedIds.has(p.id)).map(p => p.id),
    excluded: products.filter(p => p.representation && nonSolid.has(p.type)).map(p => ({
      id: p.id, type: p.type,
      reason: p.type === 'IfcOpeningElement' ? 'opening_boolean_operand' : p.type === 'IfcSpace' ? 'space_volume_not_physical_solid' : 'annotation_not_body_mesh',
    })),
    noRepresentation: products.filter(p => !p.representation).map(p => p.id),
  };
}
export function validReference(ref, version, records) {
  return !!ref && ref.version === version && records.has(Number(ref.id));
}
export function sourceLabel(p) {
  return p?.name?.trim() || (p ? t('value.unnamedObject',{type:p.type,id:p.id}) : t('value.unknownObject'));
}
export function compatibleFrame(b) {
  return !!b && ['min', 'max'].every(k => b[k]?.length === 3 && b[k].every(Number.isFinite)) &&
    b.max.every((x, i) => x >= b.min[i]) && b.max.some((x, i) => x > b.min[i]);
}
