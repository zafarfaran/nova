// Export all components for easier imports
export { ClientTable, type ClientRow } from "./ClientTable";
export { DetailPanel } from "./DetailPanel";
export { QuickMetrics, type DashboardMetrics } from "./QuickMetrics";
export { Sidebar } from "./Sidebar";
export { TopHeader } from "./TopHeader";
export { ClientFlowDiagram, ClientFlowIndicator, getClientStage, hasBlockingValidationIssues, type FlowStage } from "./ClientFlowDiagram";
export { DocumentVerification, getMockVerificationData, type DocumentVerificationData, type ValidationResult, type VerificationSummary } from "./DocumentVerification";
export { FlaggedDocuments, FlaggedDocumentsBadge, type FlaggedDocument, type FlaggedValidationResult, type FlaggedDocumentsSummary, type Severity, type ReviewAction, type AIReasoning } from "./FlaggedDocuments";
export { CreateClientForm } from "./CreateClientForm";