import config from '../../circuit.config.ts';
import type { CircuitConfig } from '@takazudo/zudo-circuit-doc/config';
import type { ComponentReferencesDescriptor, InventoryLine, PublicPlacement, PublicRecordIdentity, PublicRecordReference, PublicPackagePreview, InstanceSelection } from '@takazudo/zudo-circuit-doc';
const compatibleConfig: CircuitConfig = config;
const placements: PublicPlacement[] = [{ board: 'a' as PublicPlacement['board'], refdes: 'R1' as PublicPlacement['refdes'], dnp: true }];
// 0.3.0: the descriptor exists only for a published package, so the footprint card is required;
// an unavailable document is an explicit labelled reason, and the model stays independently optional.
const optionalCards: ComponentReferencesDescriptor = { version: 1, document: { label: 'Document unavailable', reason: 'No reviewed manufacturer document.' }, footprint: { name: 'TEST', assetUrl: '/assets/component-previews/footprints/TEST.svg' }, modelDescriptor: null };
const unavailableReason: PublicRecordReference['documentUnavailableReason'] = 'No reviewed manufacturer document.' as NonNullable<PublicRecordReference['documentUnavailableReason']>;
const deniedOwner: PublicRecordIdentity['ownerSkill'] = null;
const deniedMembership: PublicPackagePreview['recordIds'] = null;
const unavailableDocument: PublicRecordReference['document'] = null;
const unavailableModel: PublicPackagePreview['modelPath'] = null;
const lineWithoutLegacyDnp: Pick<InventoryLine, 'placements'> = {placements: [{board:'a',refdes:'R1',dnp:false}]};
const exceptions: InstanceSelection['documentExceptions'] = [{recordId:'rec-example',reason:'No reviewed manufacturer document.'}];
void [compatibleConfig,placements,optionalCards,deniedOwner,deniedMembership,unavailableDocument,unavailableModel,unavailableReason,lineWithoutLegacyDnp,exceptions];
