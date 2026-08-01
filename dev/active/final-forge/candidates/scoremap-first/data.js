/* BidPilot reference data.
 *
 * Every record below is taken from the product's existing fixtures and the
 * outputs of the existing deterministic functions:
 *   fixtures.TENDERS / fixtures.SUPPLIER_PROFILES
 *   policy.pursue_status              -> status
 *   pursuit.build_pursuit_brief       -> score map, win positions, next actions
 *   pursuit._blueprint                -> section claim / assets / owner
 *   proposal_writer._strategy_markdown-> draft preview
 *   proposal_writer.red_team_proposal -> findings
 *   proposal_writer.build_gap_closure_plan -> gap tasks
 *   bid_room.BidRoomStore             -> saved run record
 *
 * Contract value and submission deadline are NOT fields of the tender
 * contract, so they are shown in the product's own review idiom rather than
 * borrowed from the unrelated simulation records.
 */

const POLICY_VERSION = '2026-08-02.v1';

const NOT_IN_CONTRACT = 'Requires review from the source document.';

const SCENARIOS = {

  /* ------------------------------------------------------------ PURSUE */
  pursue: {
    status: 'PURSUE',
    tone: 'positive',
    statusSentence:
      'No missing eligibility requirement and no delivery-capacity shortfall. Two comparable projects meet the policy threshold, so proposal generation is open.',
    tender: {
      id: 'G2B-REPLAY-DATA-QUALITY',
      title: 'Public data quality and API continuity service',
      buyerObjective: 'Improve public-data reliability while keeping citizen-facing APIs stable.',
      promisedOutcome: 'a measured data-quality improvement and a maintained api operating model',
      tags: ['public-data', 'data-quality', 'api-operations'],
      eligibility: ['SME confirmation', 'Information-system maintenance certificate'],
      deliveryHours: 720,
      version: 'fixture:G2B-REPLAY-DATA-QUALITY:v1'
    },
    supplier: {
      id: 'supplier-northstar',
      name: 'Northstar Systems',
      credentials: ['SME confirmation', 'Information-system maintenance certificate'],
      availableHours: 900,
      people: ['Mina Lee — Public data delivery lead', 'Jun Park — API operations architect'],
      comparable: 2,
      comparableTitles: ['City Open Data Reliability Program', 'Citizen API Service Transition']
    },
    missing: [],
    capacityGap: 0,
    dims: [
      { label: 'Eligibility', value: 'Met', tone: 'positive', detail: '0 of 2 required credentials missing' },
      { label: 'Capacity', value: 'Met', tone: 'positive', detail: '900 available against 720 planned hours' },
      { label: 'Commercial fit', value: 'Not assessed', tone: 'warning', detail: 'Contract value is not part of the tender contract' },
      { label: 'Evidence strength', value: 'Above threshold', tone: 'positive', detail: '2 comparable projects; 90 of 100 weighted points covered' }
    ],
    rows: [
      {
        criterion: 'Technical approach', weight: 40,
        readiness: 'Covered', readinessTone: 'covered',
        asset: 'City Open Data Reliability Program', assetKind: 'Past project',
        gap: 'None recorded', gapTone: 'none',
        proof: [
          'City Open Data Reliability Program — reduced recurring data defects and introduced API change control.',
          'Citizen API Service Transition — transferred API support without a public-service interruption.'
        ]
      },
      {
        criterion: 'Comparable delivery', weight: 30,
        readiness: 'Covered', readinessTone: 'covered',
        asset: 'Citizen API Service Transition', assetKind: 'Past project',
        gap: 'None recorded', gapTone: 'none',
        proof: [
          'Citizen API Service Transition — transferred API support without a public-service interruption.',
          'City Open Data Reliability Program — reduced recurring data defects and introduced API change control.'
        ]
      },
      {
        criterion: 'Delivery team', weight: 20,
        readiness: 'Covered', readinessTone: 'covered',
        asset: 'Mina Lee, Jun Park', assetKind: 'Named delivery people',
        gap: 'None recorded', gapTone: 'none',
        proof: [
          'Mina Lee — Public data delivery lead.',
          'Jun Park — API operations architect.'
        ]
      },
      {
        criterion: 'Price', weight: 10,
        readiness: 'Open', readinessTone: 'open',
        asset: 'No asset in the supplier profile', assetKind: 'Unbound',
        gap: 'Commercial response not authored', gapTone: 'warning',
        proof: ['Commercial response is reconciled with the planned delivery hours before submission.']
      }
    ],
    positions: [
      {
        title: 'Technical approach',
        targets: ['Technical approach', 'Comparable delivery'],
        proof: [
          { label: 'City Open Data Reliability Program', kind: 'Past project', detail: 'Reduced recurring data defects and introduced API change control.' },
          { label: 'Citizen API Service Transition', kind: 'Past project', detail: 'Transferred API support without a public-service interruption.' },
          { label: 'SME confirmation', kind: 'Credential', detail: 'Available in the selected supplier profile.' }
        ],
        weakness: null, mitigation: null
      },
      {
        title: 'Comparable delivery',
        targets: ['Comparable delivery', 'Delivery team'],
        proof: [
          { label: 'City Open Data Reliability Program', kind: 'Past project', detail: 'Reduced recurring data defects and introduced API change control.' },
          { label: 'Citizen API Service Transition', kind: 'Past project', detail: 'Transferred API support without a public-service interruption.' },
          { label: 'SME confirmation', kind: 'Credential', detail: 'Available in the selected supplier profile.' }
        ],
        weakness: null, mitigation: null
      },
      {
        title: 'Operational continuity',
        targets: ['Comparable delivery', 'Delivery team'],
        proof: [
          { label: 'City Open Data Reliability Program', kind: 'Past project', detail: 'Reduced recurring data defects and introduced API change control.' },
          { label: 'Citizen API Service Transition', kind: 'Past project', detail: 'Transferred API support without a public-service interruption.' },
          { label: 'SME confirmation', kind: 'Credential', detail: 'Available in the selected supplier profile.' }
        ],
        weakness: null, mitigation: null
      }
    ],
    blueprintAssets: ['City Open Data Reliability Program', 'Citizen API Service Transition'],
    nextActions: ['Select a Win Position.', 'Assign the proposal blueprint owners.'],
    gapTasks: [],
    savedRun: {
      runId: 'b7f4c0d2-3a19-4e6c-9f52-8c1d0a6e5b34',
      createdAt: 'Saved earlier in this Bid Room',
      newRunId: '4e1a92c7-6d05-42b8-a3f1-70b9e2d84c16',
      newCreatedAt: 'Saved from this build',
      provider: 'local-development-adapter',
      state: 'not-executed-in-snowflake-or-coco',
      steps: ['pursuit', 'strategy', 'proposal', 'red-team', 'task-plan']
    }
  },

  /* ------------------------------------------------------------ REVIEW */
  review: {
    status: 'REVIEW',
    tone: 'warning',
    statusSentence:
      'Eligibility and capacity both pass, but only one comparable project is on file against the two required by the pursuit policy. Proposal generation stays closed until the evidence gap is validated.',
    tender: {
      id: 'G2B-REPLAY-ANALYTICS',
      title: 'Municipal analytics governance service',
      buyerObjective: 'Give policy teams governed analytics they can operate after handoff.',
      promisedOutcome: 'a governed analytics service with a practical operating handoff',
      tags: ['analytics', 'governance', 'public-sector'],
      eligibility: ['SME confirmation'],
      deliveryHours: 520,
      version: 'fixture:G2B-REPLAY-ANALYTICS:v1'
    },
    supplier: {
      id: 'supplier-atlas',
      name: 'Atlas Advisory',
      credentials: ['SME confirmation'],
      availableHours: 560,
      people: ['Dana Cho — Analytics strategy lead'],
      comparable: 1,
      comparableTitles: ['Commercial Analytics Modernization']
    },
    missing: [],
    capacityGap: 0,
    dims: [
      { label: 'Eligibility', value: 'Met', tone: 'positive', detail: '0 of 1 required credential missing' },
      { label: 'Capacity', value: 'Met', tone: 'positive', detail: '560 available against 520 planned hours' },
      { label: 'Commercial fit', value: 'Not assessed', tone: 'warning', detail: 'Contract value is not part of the tender contract' },
      { label: 'Evidence strength', value: 'Below threshold', tone: 'warning', detail: '1 comparable project against the 2 the policy requires' }
    ],
    rows: [
      {
        criterion: 'Comparable delivery', weight: 45,
        readiness: 'Partial', readinessTone: 'partial',
        asset: 'Commercial Analytics Modernization', assetKind: 'Past project',
        gap: '1 of 2 comparable projects required by the policy', gapTone: 'warning',
        proof: ['Commercial Analytics Modernization — established a commercial analytics governance model.']
      },
      {
        criterion: 'Team capability', weight: 25,
        readiness: 'Partial', readinessTone: 'partial',
        asset: 'Dana Cho', assetKind: 'Named delivery lead',
        gap: 'One named delivery person on the profile', gapTone: 'warning',
        proof: ['Dana Cho — Analytics strategy lead.']
      },
      {
        criterion: 'Operating handoff', weight: 20,
        readiness: 'Open', readinessTone: 'open',
        asset: 'No matching asset in the profile', assetKind: 'Unbound',
        gap: 'No public-sector operating-handoff evidence recorded', gapTone: 'critical',
        proof: ['No supplier asset is bound to this criterion.']
      },
      {
        criterion: 'Price', weight: 10,
        readiness: 'Open', readinessTone: 'open',
        asset: 'No asset in the supplier profile', assetKind: 'Unbound',
        gap: 'Commercial response not authored', gapTone: 'warning',
        proof: ['Commercial response is reconciled with the planned delivery hours before submission.']
      }
    ],
    positions: [
      {
        title: 'Comparable delivery',
        targets: ['Comparable delivery', 'Team capability'],
        proof: [
          { label: 'Commercial Analytics Modernization', kind: 'Past project', detail: 'Established a commercial analytics governance model.' },
          { label: 'SME confirmation', kind: 'Credential', detail: 'Available in the selected supplier profile.' },
          { label: 'Dana Cho', kind: 'Delivery lead', detail: 'Analytics strategy lead.' }
        ],
        weakness: 'Limited directly comparable delivery history',
        mitigation: 'Confirm an additional reference and assign an executive delivery reviewer before pursuing.'
      },
      {
        title: 'Team capability',
        targets: ['Team capability', 'Operating handoff'],
        proof: [
          { label: 'Commercial Analytics Modernization', kind: 'Past project', detail: 'Established a commercial analytics governance model.' },
          { label: 'SME confirmation', kind: 'Credential', detail: 'Available in the selected supplier profile.' },
          { label: 'Dana Cho', kind: 'Delivery lead', detail: 'Analytics strategy lead.' }
        ],
        weakness: 'Limited directly comparable delivery history',
        mitigation: 'Confirm an additional reference and assign an executive delivery reviewer before pursuing.'
      },
      {
        title: 'Operational continuity',
        targets: ['Team capability', 'Operating handoff'],
        proof: [
          { label: 'Commercial Analytics Modernization', kind: 'Past project', detail: 'Established a commercial analytics governance model.' },
          { label: 'SME confirmation', kind: 'Credential', detail: 'Available in the selected supplier profile.' },
          { label: 'Dana Cho', kind: 'Delivery lead', detail: 'Analytics strategy lead.' }
        ],
        weakness: 'Limited directly comparable delivery history',
        mitigation: 'Confirm an additional reference and assign an executive delivery reviewer before pursuing.'
      }
    ],
    blueprintAssets: ['Commercial Analytics Modernization'],
    nextActions: ['Validate the comparable-project gap.', 'Add a delivery reference before authoring a proposal.'],
    gapTasks: [
      { gap: 'Comparable delivery evidence', action: 'Validate another directly comparable reference and its buyer outcome.', owner: 'Evidence owner' }
    ],
    blockedTitle: 'Proposal generation is held for review',
    blockedDesc: 'The pursuit policy returned REVIEW. One comparable project is on file against the two the policy requires, so the strategy-led proposal is not generated.',
    blockedTone: 'warning',
    savedRun: null
  },

  /* ------------------------------------------------------------- NO-GO */
  nogo: {
    status: 'NO-GO',
    tone: 'critical',
    statusSentence:
      'One mandatory eligibility requirement is missing and the delivery plan is short by 160 hours. The pursuit policy blocks this opportunity outright.',
    tender: {
      id: 'G2B-REPLAY-DATA-QUALITY',
      title: 'Public data quality and API continuity service',
      buyerObjective: 'Improve public-data reliability while keeping citizen-facing APIs stable.',
      promisedOutcome: 'a measured data-quality improvement and a maintained api operating model',
      tags: ['public-data', 'data-quality', 'api-operations'],
      eligibility: ['SME confirmation', 'Information-system maintenance certificate'],
      deliveryHours: 720,
      version: 'fixture:G2B-REPLAY-DATA-QUALITY:v1'
    },
    supplier: {
      id: 'supplier-atlas',
      name: 'Atlas Advisory',
      credentials: ['SME confirmation'],
      availableHours: 560,
      people: ['Dana Cho — Analytics strategy lead'],
      comparable: 0,
      comparableTitles: []
    },
    missing: ['Information-system maintenance certificate'],
    capacityGap: 160,
    dims: [
      { label: 'Eligibility', value: 'Blocked', tone: 'critical', detail: 'Missing: Information-system maintenance certificate' },
      { label: 'Capacity', value: 'Blocked', tone: 'critical', detail: '160-hour shortfall against 720 planned hours' },
      { label: 'Commercial fit', value: 'Not assessed', tone: 'warning', detail: 'Contract value is not part of the tender contract' },
      { label: 'Evidence strength', value: 'None', tone: 'critical', detail: '0 comparable projects match the tender scope tags' }
    ],
    rows: [
      {
        criterion: 'Technical approach', weight: 40,
        readiness: 'Open', readinessTone: 'open',
        asset: 'No tag-matching asset', assetKind: 'Unbound',
        gap: 'No public-data or API delivery evidence on the profile', gapTone: 'critical',
        proof: ['No supplier asset matches the tender scope tags.']
      },
      {
        criterion: 'Comparable delivery', weight: 30,
        readiness: 'Open', readinessTone: 'open',
        asset: 'No tag-matching asset', assetKind: 'Unbound',
        gap: '0 of 2 comparable projects required by the policy', gapTone: 'critical',
        proof: ['No supplier asset matches the tender scope tags.']
      },
      {
        criterion: 'Delivery team', weight: 20,
        readiness: 'Partial', readinessTone: 'partial',
        asset: 'Dana Cho', assetKind: 'Named delivery lead',
        gap: 'One named delivery person against a 720-hour plan', gapTone: 'warning',
        proof: ['Dana Cho — Analytics strategy lead.']
      },
      {
        criterion: 'Price', weight: 10,
        readiness: 'Open', readinessTone: 'open',
        asset: 'No asset in the supplier profile', assetKind: 'Unbound',
        gap: 'Commercial response not authored', gapTone: 'warning',
        proof: ['Commercial response is reconciled with the planned delivery hours before submission.']
      }
    ],
    positions: [
      {
        title: 'Technical approach',
        targets: ['Technical approach', 'Comparable delivery'],
        proof: [
          { label: 'SME confirmation', kind: 'Credential', detail: 'Available in the selected supplier profile.' },
          { label: 'Dana Cho', kind: 'Delivery lead', detail: 'Analytics strategy lead.' }
        ],
        weakness: 'Limited directly comparable delivery history',
        mitigation: 'Confirm an additional reference and assign an executive delivery reviewer before pursuing.'
      },
      {
        title: 'Comparable delivery',
        targets: ['Comparable delivery', 'Delivery team'],
        proof: [
          { label: 'SME confirmation', kind: 'Credential', detail: 'Available in the selected supplier profile.' },
          { label: 'Dana Cho', kind: 'Delivery lead', detail: 'Analytics strategy lead.' }
        ],
        weakness: 'Limited directly comparable delivery history',
        mitigation: 'Confirm an additional reference and assign an executive delivery reviewer before pursuing.'
      },
      {
        title: 'Operational continuity',
        targets: ['Comparable delivery', 'Delivery team'],
        proof: [
          { label: 'SME confirmation', kind: 'Credential', detail: 'Available in the selected supplier profile.' },
          { label: 'Dana Cho', kind: 'Delivery lead', detail: 'Analytics strategy lead.' }
        ],
        weakness: 'Limited directly comparable delivery history',
        mitigation: 'Confirm an additional reference and assign an executive delivery reviewer before pursuing.'
      }
    ],
    blueprintAssets: ['SME confirmation', 'Dana Cho'],
    nextActions: ['Do not generate a proposal.', 'Resolve eligibility or delivery capacity before reopening this opportunity.'],
    gapTasks: [
      { gap: 'Information-system maintenance certificate', action: 'Verify or obtain Information-system maintenance certificate before reopening.', owner: 'Bid manager' },
      { gap: '160 delivery hours', action: 'Secure named delivery capacity and rerun the pursuit policy.', owner: 'Delivery lead' }
    ],
    blockedTitle: 'Proposal generation blocked',
    blockedDesc: 'The pursuit policy returned NO-GO. Proposal generation raises an error for this opportunity until eligibility and capacity are resolved.',
    blockedTone: 'critical',
    savedRun: null
  }
};
