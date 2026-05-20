import { PropsWithChildren } from "react";

import { WorkspaceShell } from "@/components/workspace-shell";

export default function WorkspaceLayout({ children }: PropsWithChildren) {
  return <WorkspaceShell>{children}</WorkspaceShell>;
}
